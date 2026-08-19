from src.domain.model.courseModel import CourseModel
from src.infraestructure.dto.database.courseDto import CoursesDto


def courseModelToCoursesDto(course: CourseModel) -> CoursesDto:
    return CoursesDto(
        source_id=course.sourceId,
        title=course.title,
        url=course.url,
        uni_countries=course.country,
        disciplinary_fields=course.disciplinaryFields,
        course_university=course.university,
        uni_languages=course.language,
        start_class_date=course.startClassDate,
        end_class_date=course.endClassDate,
        start_inscription_date=course.startInscriptionDate,
        end_inscription_date=course.endInscriptionDate,
        description=course.description,
        study_hours=course.studyHours,
        slots=course.slots,
        modified_date=course.modifiedDate,
    )