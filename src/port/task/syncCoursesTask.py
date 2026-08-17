import logging
import os

from dotenv import load_dotenv

from src.aplication.syncCoursesUseCase import SyncCoursesUseCase
from src.infraestructure.repositoryImp.emoviesCoursesRepositoryImp import EmoviesCoursesRepositoryImp


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    load_dotenv()

    if not os.getenv("DB_URL"):
        raise RuntimeError("Falta variable de entorno DB_URL")

    courseRepository = EmoviesCoursesRepositoryImp()
    syncCoursesUseCase = SyncCoursesUseCase(courseRepository)

    inserted = syncCoursesUseCase.execute()
    logging.info("syncCoursesTask: sincronización completada con %d cursos", inserted)


if __name__ == "__main__":
    main()