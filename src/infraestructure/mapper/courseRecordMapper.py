from typing import Dict, List

from src.domain.model.courseModel import CourseRecordDto, ShowCourseModel


def rowToCourseRecordDto(row: dict) -> CourseRecordDto:
    """Convierte una fila plana de la consulta de cursos en su CourseRecordDto.

    La consulta trae cada columna con un alias explicito, asi que cada clave de
    la fila corresponde a un campo del DTO. Se lee con row.get para que una
    columna ausente quede en None en vez de romper el mapeo.
    """
    return CourseRecordDto(
        id=row.get("id"),
        title=row.get("title"),
        description=row.get("description"),
        siteUrl=row.get("site_url"),
        modality=row.get("modality"),
        credits=row.get("credits"),
        enrollmentStart=row.get("enrollment_start"),
        enrollmentEnd=row.get("enrollment_end"),
        courseStart=row.get("course_start"),
        courseEnd=row.get("course_end"),
        totalSeats=row.get("total_seats"),
        availableSeats=row.get("available_seats"),
        updatedAt=row.get("updated_at"),
        campusName=row.get("campus_name"),
        universityName=row.get("university_name"),
        cityName=row.get("city_name"),
        countryIsoCode=row.get("country_iso_code"),
        countryName=row.get("country_name"),
        languageCode=row.get("language_code"),
        languageName=row.get("language_name"),
        academicLevelId=row.get("academic_level_id"),
        academicLevelName=row.get("academic_level_name"),
        sourceName=row.get("source_name"),
    )


def courseRecordToShowCourseModel(
    record: CourseRecordDto, knowledgeAreas: List[str]
) -> ShowCourseModel:
    """Arma el modelo que se envia por Telegram a partir del registro y sus areas.

    Los catalogos ya vienen resueltos en el registro (nombre de la fuente, de la
    universidad, del pais, del idioma y del nivel academico), asi que aqui solo
    se renombran los campos al idioma del mensaje. totalSeats, modality y credits
    se leen del catalogo pero no se muestran: el mensaje conserva la forma actual.
    """
    return ShowCourseModel(
        source=record.sourceName,
        university=record.universityName,
        country=record.countryName,
        language=record.languageName,
        disciplinaryFields=list(knowledgeAreas) if knowledgeAreas else None,
        courseLevel=record.academicLevelName,
        title=record.title,
        url=record.siteUrl,
        startClassDate=record.courseStart,
        endClassDate=record.courseEnd,
        startInscriptionDate=record.enrollmentStart,
        endInscriptionDate=record.enrollmentEnd,
        description=record.description,
        slots=record.availableSeats,
        updatedAt=record.updatedAt,
    )


def rowsToCourseRecordDtos(rows: List[Dict[str, object]]) -> List[CourseRecordDto]:
    """Mapea todas las filas de la consulta de cursos."""
    return [rowToCourseRecordDto(row) for row in rows]