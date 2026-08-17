from datetime import date

import logging
from src.domain.courseRepository import CourseFilters
from src.infraestructure.emoviesCoursesRepositoryImp import EmoviesCoursesRepositoryImp

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    print("llamando...")
    repo = EmoviesCoursesRepositoryImp()

    courses = repo.getCourses(CourseFilters(
        minModifiedDate=date(2026, 8, 10)
    ))

    print(courses)

if __name__ == "__main__":
    main()