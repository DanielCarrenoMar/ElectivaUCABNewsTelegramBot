from src.domain.model.courseModel import CourseModel
from src.infraestructure.dto.ausjal.ausjalCourseDto import AusjalCourseDto
from src.infraestructure.mapper.ausjal.ausjalCatalogTranslator import ausjalTextToAppIdCatalog

def ausjalCourseDtoToCourseModel(dto: AusjalCourseDto) -> CourseModel:
    return CourseModel(
        sourceId=2, # id de Ausjal,
        title=dto.title,
        courseLevel=ausjalTextToAppIdCatalog("education_levels", dto.courseLevels),
        university=ausjalTextToAppIdCatalog("universities", dto.courseUniversity),
        url=dto.documentUrl or "",
        country=ausjalTextToAppIdCatalog("countries", dto.uniCountries),
        language=None,
        disciplinaryField=ausjalTextToAppIdCatalog("disciplinary_fields", dto.disciplinaryField),
        startClassDate=dto.startClassDate,
        endClassDate=dto.endClassDate,
        startInscriptionDate=dto.startInscriptionDate,
        endInscriptionDate=dto.endInscriptionDate,
        studyHours=dto.study_hours,
        slots=dto.slots,
        modifiedDate=dto.modifiedDate,
    )