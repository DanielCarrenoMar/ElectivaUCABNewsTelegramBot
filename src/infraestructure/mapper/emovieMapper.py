from datetime import date, datetime
from typing import Optional

from src.domain.model.courseModel import CourseModel, EducationLevelEnum
from infraestructure.dto.emovies.emovieApiResponseDto import EmovieApiCourseDto
from infraestructure.dto.emovies.emovieswebScraperCourseDto import EmoviesWebScraperCourseDto

COURSE_URL_BASE = "https://emovies.oui-iohe.org/nuestros-cursos/"

DEFAULT_TITLE = "Sin título"
DEFAULT_EDUCATION_LEVEL = EducationLevelEnum.UNDERGRADUATE
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


def emovieDtoToCourseModel(
    apiCourseDto: EmovieApiCourseDto,
    webScraperCourseDto: Optional[EmoviesWebScraperCourseDto] = None,
) -> CourseModel:
    detail = webScraperCourseDto or EmoviesWebScraperCourseDto()

    return CourseModel(
        title=apiCourseDto.post_name or DEFAULT_TITLE,
        educationLevel=_parseEducationLevel(detail.educationLevel),
        url=_courseUrl(apiCourseDto),
        country=detail.country or DEFAULT_COUNTRY,
        language=detail.language or DEFAULT_LANGUAGE,
        startClassDate=detail.startClassDate or DEFAULT_DATE,
        endClassDate=detail.endClassDate or DEFAULT_DATE,
        startIncriptionDate=detail.startInscriptionDate or DEFAULT_DATE,
        endInscriptionDate=detail.endInscriptionDate or DEFAULT_DATE,
        description=detail.description or apiCourseDto.post_content or DEFAULT_DESCRIPTION,
        studyHours=detail.studyHours if detail.studyHours is not None else DEFAULT_STUDY_HOURS,
        slots=detail.slots if detail.slots is not None else DEFAULT_SLOTS,
    )