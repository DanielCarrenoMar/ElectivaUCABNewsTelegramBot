import logging
import os

from dotenv import load_dotenv

from src.aplication.syncCoursesUseCase import SyncCoursesUseCase
from src.infraestructure.repositoryImp.emoviesCoursesRepositoryImp import EmoviesCoursesRepositoryImp
from src.port.task.task import log_task_duration


@log_task_duration
def syncCoursesTask():
    load_dotenv()

    if not os.getenv("DB_URL"):
        raise RuntimeError("Falta variable de entorno DB_URL")

    courseRepository = EmoviesCoursesRepositoryImp()
    syncCoursesUseCase = SyncCoursesUseCase(courseRepository)

    inserted = syncCoursesUseCase.execute()
    logging.info("syncCoursesTask: sincronización completada con %d cursos", inserted)


if __name__ == "__main__":
    syncCoursesTask()