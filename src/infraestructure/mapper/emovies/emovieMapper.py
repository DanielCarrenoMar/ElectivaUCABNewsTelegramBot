from datetime import date, datetime
from typing import Optional, Union

from src.domain.model.courseModel import EducationLevelEnum
from src.infraestructure.dto.database.courseDto import CoursesDto
from src.infraestructure.dto.emovies.emovieApiResponseDto import EmovieApiCourseDto, EmovieApiDataDto
from src.infraestructure.dto.emovies.emovieswebScraperCourseDto import EmoviesWebScraperCourseDto
from src.infraestructure.mapper.emovies.emoviesCatalogTranslator import emoviesIdCatalogToAppIdCatalog

from bs4 import BeautifulSoup

COURSE_URL_BASE = "https://emovies.oui-iohe.org/nuestros-cursos/"

DEFAULT_TITLE = "Sin título"
DEFAULT_EDUCATION_LEVEL = EducationLevelEnum.UNDERGRADUATE
DEFAULT_UNIVERSITY = ""
DEFAULT_COUNTRY = ""
DEFAULT_LANGUAGE = ""
DEFAULT_DESCRIPTION = ""
# Valores por defecto pendientes del scraper web: aún no se pueden rellenar
# con la respuesta de la API, así que se asignan marcadores de posición.
DEFAULT_DATE = date.min
DEFAULT_STUDY_HOURS = 0
DEFAULT_SLOTS = 0


def parseApiDatetime(value: Optional[str]) -> Optional[date]:
    """Convierte una fecha de la API ('2026-05-12 09:14:21' o ISO) a date."""
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _courseUrl(apiCourseDto: EmovieApiCourseDto) -> str:
    slug = apiCourseDto.post_name or ""
    if slug:
        return f"{COURSE_URL_BASE}{slug}"
    return apiCourseDto.guid or ""


def _parseEducationLevel(value: Optional[str]) -> EducationLevelEnum:
    if not value:
        return DEFAULT_EDUCATION_LEVEL

    try:
        return EducationLevelEnum(value)
    except ValueError:
        return DEFAULT_EDUCATION_LEVEL


def _courseModifiedDate(apiCourseDto: EmovieApiCourseDto) -> date:
    parsedDates = [
        parsedDate
        for parsedDate in (
            parseApiDatetime(apiCourseDto.post_date),
            parseApiDatetime(apiCourseDto.post_modified),
        )
        if parsedDate is not None
    ]

    if not parsedDates:
        return date.min

    return max(parsedDates)

def _extractHtmlData(html:str):
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.find_all("div", class_="item--course")
    
    cardsInfo = []

    for card in cards:
        cardClassz = card.get("class", [])

        diciplinary = ""
        level = ""
        language = ""

        for cardClass in cardClassz:
            if cardClass.startswith("course_disciplinary_new"):
                diciplinary = cardClass.split("-")[1]
            elif cardClass.startswith("course_level"):
                level = cardClass.split("-")[1]
            elif cardClass.startswith("university_language"):
                language = cardClass.split("-")[1]

        cardsInfo.append((diciplinary, level, language))

    return cardsInfo


def emovieResponseToCourseDtos(
    apiDataDto: EmovieApiDataDto,
    webScraperCourseDto: Optional[EmoviesWebScraperCourseDto],
) -> list[CoursesDto]:
    detail = webScraperCourseDto or EmoviesWebScraperCourseDto()

    courseDtos: list[CoursesDto] = [
        CoursesDto(
            external_id=course.ID,
            title=course.post_name,
            url=_courseUrl(course),
            modified_date=_courseModifiedDate(course),
        )
        for course in apiDataDto.courses.posts
    ]

    for i, (disciplinary, level, language) in enumerate(_extractHtmlData(apiDataDto.courses_html)):
        courseDtos[i] = courseDtos[i].model_copy(
            update={
                # TODO: traducir los slugs del HTML a IDs de catálogo
                "disciplinary_field": None,
                "course_levels": None,
                "uni_languages": None,
            }
        )

    return courseDtos
