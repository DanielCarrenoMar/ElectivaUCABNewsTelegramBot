from datetime import date, datetime
from typing import Optional, Union

from src.domain.model.courseModel import EducationLevelEnum
from src.infraestructure.dto.database.courseDto import CoursesDto
from src.infraestructure.dto.emovies.emovieApiResponseDto import EmovieApiCourseDto, EmovieApiDataDto
from src.infraestructure.dto.emovies.emovieswebScraperCourseDto import EmoviesWebScraperCourseDto
from src.infraestructure.mapper.emoviesCatalogTranslator import EmoviesCatalogTranslator

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


def _extractIntCode(value: Optional[Union[str, bool]]) -> Optional[int]:
    """Extrae un código numérico de un valor de la API ('280', '86')."""
    if not isinstance(value, str) or not value.isdigit():
        return None

    return int(value)


def _catalogCode(data: Optional[EmovieApiDataDto], field: str) -> Optional[str]:
    if data is None:
        return None

    value = getattr(data, field, None)
    if _extractIntCode(value) is None:
        return None

    return str(value)


def emovieResponseToCourseDto(
    apiCourseDto: EmovieApiCourseDto,
    apiDataDto: Optional[EmovieApiDataDto],
    webScraperCourseDto: Optional[EmoviesWebScraperCourseDto],
    translator: Optional[EmoviesCatalogTranslator],
) -> CoursesDto:
    detail = webScraperCourseDto or EmoviesWebScraperCourseDto()
    data = apiDataDto

    if translator is not None:
        uni_countries = translator.codeToDbId("countries", _catalogCode(data, "uni_countries"))
        course_university = translator.codeToDbId("universities", _catalogCode(data, "course_university"))
        uni_languages = translator.codeToDbId("languages", _catalogCode(data, "uni_languages"))
        disciplinary_field = translator.codeToDbId(
            "disciplinary_fields",
            _catalogCode(data, "disciplinary_field"),
        )
        course_levels = translator.codeToDbId("course_levels", _catalogCode(data, "course_levels"))
    else:
        uni_countries = None
        course_university = None
        uni_languages = None
        disciplinary_field = None
        course_levels = None

    return CoursesDto(
        external_id=apiCourseDto.ID,
        title=apiCourseDto.post_name or DEFAULT_TITLE,
        url=_courseUrl(apiCourseDto),
        uni_countries=uni_countries,
        disciplinary_field=disciplinary_field,
        course_university=course_university,
        uni_languages=uni_languages,
        course_levels=course_levels,
        start_class_date=detail.startClassDate or DEFAULT_DATE,
        end_class_date=detail.endClassDate or DEFAULT_DATE,
        start_inscription_date=detail.startInscriptionDate or DEFAULT_DATE,
        end_inscription_date=detail.endInscriptionDate or DEFAULT_DATE,
        description=detail.description or apiCourseDto.post_content or DEFAULT_DESCRIPTION,
        study_hours=detail.studyHours if detail.studyHours is not None else DEFAULT_STUDY_HOURS,
        slots=detail.slots if detail.slots is not None else DEFAULT_SLOTS,
        modified_date=_courseModifiedDate(apiCourseDto),
    )