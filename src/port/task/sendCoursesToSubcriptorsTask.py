import logging
import os

from dotenv import load_dotenv
from telebot import TeleBot

from src.aplication.sendCourseToSubcriptorsUseCase import SendCourseToSubcriptorsUseCase
from src.infraestructure.repositoryImp.telegramNotifierRepositoryImp import TelegramNotifierRepositoryImp
from src.port.task.task import log_task_duration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s",
    force=True,
)


@log_task_duration
def sendCoursesToSubcriptorsTask():
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Falta variable de entorno TELEGRAM_BOT_TOKEN")
    if not os.getenv("DB_URL"):
        raise RuntimeError("Falta variable de entorno DB_URL")

    bot = TeleBot(token, parse_mode="HTML")
    notifier = TelegramNotifierRepositoryImp(bot)
    sendCourseToAllUseCase = SendCourseToSubcriptorsUseCase(notifier)

    totalSent = sendCourseToAllUseCase.execute()
    logging.info("sendCoursesToSubcriptorsTask: total de cursos enviados %d", totalSent)


if __name__ == "__main__":
    sendCoursesToSubcriptorsTask()