import logging
import os

from dotenv import load_dotenv

from src.aplication.syncCoursesUseCase import SyncCoursesUseCase
from infraestructure.repositoryImp.emoviesCoursesRepositoryImp import EmoviesCoursesRepositoryImp
from infraestructure.mapper.emovies.emoviesCatalogTranslator import EmoviesCatalogTranslator
from infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    load_dotenv()

    if not os.getenv("DB_URL"):
        raise RuntimeError("Falta variable de entorno DB_URL")

    courseRepository = EmoviesCoursesRepositoryImp()
    databaseRepository = PostgresDatabaseRepositoryImp()
    syncCoursesUseCase = SyncCoursesUseCase(courseRepository, databaseRepository)

    inserted = syncCoursesUseCase.execute()
    logging.info("syncCoursesTask: sincronización completada con %d cursos", inserted)


if __name__ == "__main__":
    main()