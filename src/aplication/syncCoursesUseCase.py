from src.domain.repository.sourceRepository import CourseFilters, SourceRepository
from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp

class SyncCoursesUseCase:
    def __init__(self, courseRepository: SourceRepository):
        self._courseRepository = courseRepository
        self._databaseRepository = PostgresDatabaseRepositoryImp()

    def execute(self) -> int:
        courses = self._courseRepository.getCourses(CourseFilters())
        
        self._databaseRepository.deleteCoursesBySource(self._courseRepository.SOURCE_ID)

        inserted = self._databaseRepository.saveCourses(courses)

        return inserted