import logging

from src.domain.repository.courseRepository import CourseFilters, CourseRepository
from src.domain.repository.databaseRepository import DatabaseRepository


class SyncCoursesUseCase:
    def __init__(self, courseRepository: CourseRepository, databaseRepository: DatabaseRepository):
        self._courseRepository = courseRepository
        self._databaseRepository = databaseRepository

    def execute(self) -> int:
        courses = self._courseRepository.getCourses(CourseFilters())
        logging.info("SyncCoursesUseCase: se obtuvieron %d cursos de la fuente", len(courses))

        self._databaseRepository.deleteAllCourses()
        logging.info("SyncCoursesUseCase: se eliminaron los cursos previos de la tabla courses")

        inserted = self._databaseRepository.saveCourses(courses)
        logging.info("SyncCoursesUseCase: se insertaron %d cursos en la tabla courses", inserted)

        return inserted