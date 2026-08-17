from datetime import date

from src.domain.model.courseModel import CourseModel, EducationLevelEnum
from src.infraestructure.dto.database.courseDto import CoursesDto


def courseDtoToCourseModel(courseDto: CoursesDto, catalogNames: dict[str, dict[int, str]]) -> CourseModel:
    university = catalogNames.get("universities", {}).get(courseDto.course_university, "")
    country = catalogNames.get("countries", {}).get(courseDto.uni_countries, "")
    language = catalogNames.get("languages", {}).get(courseDto.uni_languages, "")

    levelName = catalogNames.get("course_levels", {}).get(courseDto.course_levels, "").lower()
    educationLevel = (
        EducationLevelEnum.POSTGRADUATE
        if "posgrado" in levelName or "postgraduate" in levelName
        else EducationLevelEnum.UNDERGRADUATE
    )

    return CourseModel(
        externalId=courseDto.external_id,
        title=courseDto.title or "",
        educationLevel=educationLevel,
        university=university,
        url=courseDto.url or "",
        country=country,
        language=language,
        startClassDate=courseDto.start_class_date or date.min,
        endClassDate=courseDto.end_class_date or date.min,
        startInscriptionDate=courseDto.start_inscription_date or date.min,
        endInscriptionDate=courseDto.end_inscription_date or date.min,
        description=courseDto.description or "",
        studyHours=courseDto.study_hours or 0,
        slots=courseDto.slots or 0,
        modifiedDate=courseDto.modified_date or date.min,
    )