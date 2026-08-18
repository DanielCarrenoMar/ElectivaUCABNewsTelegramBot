from datetime import date
from typing import Optional

from src.domain.model.courseModel import CourseModel, EducationLevelEnum
from src.infraestructure.dto.ausjal.ausjalCourseDto import AusjalCourseDto
from src.infraestructure.mapper.ausjal.ausjalCatalogTranslator import ausjalTextToAppIdCatalog

DEFAULT_TITLE = "Sin título"
DEFAULT_EDUCATION_LEVEL = EducationLevelEnum.UNDERGRADUATE
DEFAULT_DATE = date.min
DEFAULT_DESCRIPTION = ""
DEFAULT_STUDY_HOURS = 0
DEFAULT_SLOTS = 0

_POSTGRADUATE_KEYWORDS = ("posgrado", "doctorado", "maestria", "mestrado", "doutorado")


def _parseEducationLevel(value: Optional[str]) -> EducationLevelEnum:
    if not value:
        return DEFAULT_EDUCATION_LEVEL

    lowerValue = value.lower()
    if any(keyword in lowerValue for keyword in _POSTGRADUATE_KEYWORDS):
        return EducationLevelEnum.POSTGRADUATE

    return DEFAULT_EDUCATION_LEVEL


def ausjalCourseDtoToCourseModel(dto: AusjalCourseDto) -> CourseModel:
    return CourseModel(
        title=dto.title or DEFAULT_TITLE,
        educationLevel=_parseEducationLevel(dto.courseLevels),
        university=ausjalTextToAppIdCatalog("universities", dto.courseUniversity),
        url=dto.documentUrl or "",
        country=ausjalTextToAppIdCatalog("countries", dto.uniCountries),
        language=None,
        disciplinaryField=ausjalTextToAppIdCatalog("disciplinary_fields", dto.disciplinaryField),
        courseLevel=ausjalTextToAppIdCatalog("course_levels", dto.courseLevels),
        startClassDate=dto.startClassDate or DEFAULT_DATE,
        endClassDate=dto.endClassDate or DEFAULT_DATE,
        startInscriptionDate=dto.startInscriptionDate or DEFAULT_DATE,
        endInscriptionDate=dto.endInscriptionDate or DEFAULT_DATE,
        description=DEFAULT_DESCRIPTION,
        studyHours=dto.study_hours or DEFAULT_STUDY_HOURS,
        slots=dto.slots or DEFAULT_SLOTS,
        modifiedDate=dto.modifiedDate or DEFAULT_DATE,
    )