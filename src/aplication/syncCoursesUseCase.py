import logging

from src.domain.repository.courseRepository import CourseFilters, CourseRepository
from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


class SyncCoursesUseCase:
    def __init__(self, courseRepository: CourseRepository):
        self._courseRepository = courseRepository
        self._databaseRepository = PostgresDatabaseRepositoryImp()

    def execute(self) -> int:
        courses = self._courseRepository.getCourses(CourseFilters())
        logging.info("SyncCoursesUseCase: se obtuvieron %d cursos de la fuente", len(courses))

        self._databaseRepository.deleteAllCourses()
        logging.info("SyncCoursesUseCase: se eliminaron los cursos previos de la tabla courses")

        inserted = self._databaseRepository.saveCourses(courses)
        logging.info("SyncCoursesUseCase: se insertaron %d cursos en la tabla courses", inserted)

        return inserted