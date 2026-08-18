import logging

from telebot import TeleBot

from src.domain.model.courseModel import ShowCourseModel
from src.domain.repository.notifierRepository import notifierRepository


class TelegramNotifierRepositoryImp(notifierRepository):
    def __init__(self, bot: TeleBot):
        self._bot = bot

    def sendCourseToChat(self, chatId: int, course: ShowCourseModel) -> None:
        text = course.buildMessage()
        self._bot.send_message(
            chatId,
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        logging.info("TelegramCourseNotifier: curso '%s' enviado al chat %s", course.title, chatId)