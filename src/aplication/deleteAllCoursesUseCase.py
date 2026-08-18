from src.domain.repository.courseRepository import CourseFilters, CourseSourceRepository
from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp

class DeleteAllCoursesUseCase:
    def __init__(self):
        self._databaseRepository = PostgresDatabaseRepositoryImp()

    def execute(self) -> None:
        self._databaseRepository.deleteAllCourses()