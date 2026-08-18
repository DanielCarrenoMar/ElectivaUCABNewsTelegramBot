from datetime import date
from typing import Optional

from src.domain.model.courseModel import CourseModel, EducationLevelEnum
from src.infraestructure.dto.ausjal.ausjalCourseDto import AusjalCourseDto
from src.infraestructure.mapper.ausjal.ausjalCatalogTranslator import ausjalTextToAppIdCatalog



def ausjalCourseDtoToCourseModel(dto: AusjalCourseDto) -> CourseModel:
    return CourseModel(
        title=dto.title,
        educationLevel=ausjalTextToAppIdCatalog("education_levels", dto.educationLevel),
        university=ausjalTextToAppIdCatalog("universities", dto.courseUniversity),
        url=dto.documentUrl or "",
        country=ausjalTextToAppIdCatalog("countries", dto.uniCountries),
        language=None,
        disciplinaryField=ausjalTextToAppIdCatalog("disciplinary_fields", dto.disciplinaryField),
        courseLevel=ausjalTextToAppIdCatalog("course_levels", dto.courseLevels),
        startClassDate=dto.startClassDate,
        endClassDate=dto.endClassDate,
        startInscriptionDate=dto.startInscriptionDate,
        endInscriptionDate=dto.endInscriptionDate,
        studyHours=dto.study_hours,
        slots=dto.slots,
        modifiedDate=dto.modifiedDate,
    )