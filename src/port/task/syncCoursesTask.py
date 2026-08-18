import logging
import os

from dotenv import load_dotenv

from src.aplication.syncCoursesUseCase import SyncCoursesUseCase
from src.infraestructure.repositoryImp.emoviesCoursesRepositoryImp import EmoviesSourceRepositoryImp
from src.infraestructure.repositoryImp.ausjalCoursesRepositoryImp import AusjalSourceRepositoryImp
from src.port.task.task import log_task_duration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s",
    force=True,
)

@log_task_duration
def syncCoursesTask():
    load_dotenv()

    if not os.getenv("DB_URL"):
        raise RuntimeError("Falta variable de entorno DB_URL")

    emoviesSourceRepository = EmoviesSourceRepositoryImp()
    ausjalSourceRepository = AusjalSourceRepositoryImp()
    emoviesSyncCoursesUseCase = SyncCoursesUseCase(emoviesSourceRepository)
    ausjalSyncCoursesUseCase = SyncCoursesUseCase(ausjalSourceRepository)

    insertedEmovies = emoviesSyncCoursesUseCase.execute()
    logging.info("syncCoursesTask: sincronización con emovies completada con %d cursos", insertedEmovies)

    insertedAusjal = ausjalSyncCoursesUseCase.execute()
    logging.info("syncCoursesTask: sincronización con ausjal completada con %d cursos", insertedAusjal)


if __name__ == "__main__":
    syncCoursesTask()