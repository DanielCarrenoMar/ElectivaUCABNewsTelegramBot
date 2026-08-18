from typing import List

from src.domain.model.courseModel import CourseModel
from src.domain.repository.courseRepository import CourseFilters, CourseSourceRepository


class AusjalCoursesRepositoryImp(CourseSourceRepository):
    """Implementación pendiente del origen de cursos AUSJAL.

    El contrato ya está definido; la lógica de obtención aún no está implementada.
    """

    def getCourses(self, filters: CourseFilters) -> List[CourseModel]:
        raise NotImplementedError("La fuente AUSJAL aún no está implementada")