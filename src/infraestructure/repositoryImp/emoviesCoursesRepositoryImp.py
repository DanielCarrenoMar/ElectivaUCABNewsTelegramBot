import logging
from datetime import date
from typing import Callable, List, Optional

import requests

from src.domain.repository.courseRepository import CourseFilters, CourseRepository
from src.infraestructure.dto.database.courseDto import CoursesDto
from src.infraestructure.dto.emovies.emovieApiParamsDto import EmovieApiParamsDto
from src.infraestructure.dto.emovies.emovieApiResponseDto import (
    EmovieApiCourseDto,
    EmovieApiCoursesDto,
    EmovieApiDataDto,
    EmovieApiResponseDto,
)
from src.infraestructure.dto.emovies.emovieswebScraperCourseDto import EmoviesWebScraperCourseDto
from src.infraestructure.mapper.emovies.emoviesMapper import emovieResponseToCourseDtos, parseApiDatetime

class EmoviesCoursesRepositoryImp(CourseRepository):
    API_URL = "https://emovies.oui-iohe.org/wp-admin/admin-ajax.php"
    REQUEST_TIMEOUT_SECONDS = 30
    NO_FILTER_VALUE = "NaN"

    def __init__(
        self,
        web_scraper: Optional[Callable[[EmovieApiCourseDto], EmoviesWebScraperCourseDto]] = None,
    ):
        self._web_scraper = web_scraper

    def getCourses(self, filters: CourseFilters) -> List[CoursesDto]:
        logging.info("Obteniendo cursos con filtros: %s", filters.model_dump())
        apiParams = self._buildApiParams(filters)
        courseDtos, firstPageDataDto = self._fetchAllCourses(apiParams)
        courseDtos = self._filterByMinModifiedDate(courseDtos, filters.minModifiedDate)
        courseDtos = self._sortByDateDesc(courseDtos)

        if firstPageDataDto is None:
            raise RuntimeError("La API de eMOVIES no devolvió datos")
        mappedData = firstPageDataDto.model_copy(update={"courses": EmovieApiCoursesDto(posts=courseDtos)})
        courseDtos = emovieResponseToCourseDtos(mappedData, None)
        courses: List[CoursesDto] = []

        for courseDto in courseDtos:

            if filters.minStudyHours is not None and courseDto.study_hours < filters.minStudyHours:
                logging.debug(
                    "Curso '%s' descartado: studyHours %d < minStudyHours %d",
                    courseDto.title,
                    courseDto.study_hours,
                    filters.minStudyHours,
                )
                continue

            courses.append(courseDto)

        logging.info("getCourses devolvió %d cursos", len(courses))
        return courses

    def _buildApiParams(self, filters: CourseFilters) -> EmovieApiParamsDto:
        return EmovieApiParamsDto(
            uni_search=filters.keyword or "",
            course_levels="86" or self.NO_FILTER_VALUE,
            uni_countries=filters.country or self.NO_FILTER_VALUE,
            uni_languages=filters.language or self.NO_FILTER_VALUE,
            course_university=filters.university or self.NO_FILTER_VALUE,
            disciplinary_field="265"
        )

    def _fetchAllCourses(
        self,
        apiParams: EmovieApiParamsDto,
    ) -> tuple[List[EmovieApiCourseDto], Optional[EmovieApiDataDto]]:
        firstPageData = self._fetchPage(apiParams, 1)
        coursesPayload = firstPageData.courses
        maxNumPages = (coursesPayload.max_num_pages or firstPageData.max_num_page) or 1
        logging.info("La API de eMOVIES reporta %d páginas de cursos", maxNumPages)

        coursesById: dict[int, EmovieApiCourseDto] = {}
        for page in range(1, maxNumPages + 1):
            pageData = firstPageData if page == 1 else self._fetchPage(apiParams, page)
            for courseDto in (pageData.courses.posts if pageData.courses else []) or []:
                if courseDto.ID is not None:
                    coursesById[courseDto.ID] = courseDto

        logging.info("Se obtuvieron %d cursos únicos tras deduplicar por ID", len(coursesById))
        return list(coursesById.values()), firstPageData

    def _fetchPage(self, apiParams: EmovieApiParamsDto, page: int) -> EmovieApiDataDto:
        logging.info("Consultando página %d de la API de eMOVIES", page)
        pageParams = {**apiParams.model_dump(), "page": str(page)}
        response = requests.get(self.API_URL, params=pageParams, timeout=self.REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        payload = EmovieApiResponseDto.model_validate(response.json())
        if not payload.success:
            logging.warning("La API de eMOVIES respondió success=false en la página %d", page)
            raise ValueError("La API de eMOVIES respondió success=false")

        if payload.data is None or payload.data.courses is None:
            logging.warning("La API de eMOVIES no devolvió cursos en la página %d", page)
            raise ValueError("La API de eMOVIES no devolvió cursos")

        logging.info("Página %d devolvió %d cursos", page, len(payload.data.courses.posts))
        return payload.data

    def _filterByMinModifiedDate(
        self,
        courseDtos: List[EmovieApiCourseDto],
        minModifiedDate: Optional[date],
    ) -> List[EmovieApiCourseDto]:
        if minModifiedDate is None:
            return courseDtos

        filtered: List[EmovieApiCourseDto] = []
        for courseDto in courseDtos:
            modifiedDate = parseApiDatetime(courseDto.post_modified)
            if modifiedDate is not None and modifiedDate >= minModifiedDate:
                filtered.append(courseDto)

        logging.info(
            "Filtro por fecha mínima %s: %d cursos -> %d cursos",
            minModifiedDate,
            len(courseDtos),
            len(filtered),
        )
        return filtered

    def _sortByDateDesc(self, courseDtos: List[EmovieApiCourseDto]) -> List[EmovieApiCourseDto]:
        sortedDtos = sorted(
            courseDtos,
            key=lambda courseDto: self._courseDate(courseDto),
            reverse=True,
        )
        logging.debug("Cursos ordenados por fecha descendente: %d", len(sortedDtos))
        return sortedDtos

    def _courseDate(self, courseDto: EmovieApiCourseDto) -> date:
        parsedDates = [
            parsedDate
            for parsedDate in (
                parseApiDatetime(courseDto.post_date),
                parseApiDatetime(courseDto.post_modified),
            )
            if parsedDate is not None
        ]

        if not parsedDates:
            return date.min

        return max(parsedDates)

    def _scrapeCourseDetail(self, courseDto: EmovieApiCourseDto) -> EmoviesWebScraperCourseDto:
        """Hook para el futuro scraper web.

        Hasta que exista, devuelve un DTO vacío y el mapper usa valores por defecto.
        """
        if self._web_scraper is None:
            logging.debug(
                "Scraper web no configurado; se usarán valores por defecto para el curso %s",
                courseDto.ID,
            )
            return EmoviesWebScraperCourseDto()

        logging.debug("Scrapeando detalle web del curso %s", courseDto.ID)
        return self._web_scraper(courseDto)