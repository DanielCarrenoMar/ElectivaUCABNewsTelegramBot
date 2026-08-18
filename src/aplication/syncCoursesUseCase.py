import logging

from src.domain.repository.courseRepository import CourseFilters, CourseSourceRepository
from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


class SyncCoursesUseCase:
    def __init__(self, courseRepository: CourseSourceRepository):
        self._courseRepository = courseRepository
        self._databaseRepository = PostgresDatabaseRepositoryImp()

    def execute(self) -> int:
        courses = self._courseRepository.getCourses(CourseFilters())

        self._databaseRepository.deleteAllCourses()

        inserted = self._databaseRepository.saveCourses(courses)

        return inserted