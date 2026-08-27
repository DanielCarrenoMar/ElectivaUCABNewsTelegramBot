import logging

from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from src.domain.model.courseModel import ShowCourseModel
from src.domain.repository.notifierRepository import InvalidTelegramChatError, notifierRepository


class TelegramNotifierRepositoryImp(notifierRepository):
    def __init__(self, bot: TeleBot):
        self._bot = bot

    def sendCourseToChat(self, chatId: int, course: ShowCourseModel) -> None:
        text = course.buildMessage()
        try:
            self._bot.send_message(
                chatId,
                text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except ApiTelegramException as error:
            if self._isInvalidChatError(error):
                raise InvalidTelegramChatError(chatId, str(error)) from error
            raise
        logging.info("TelegramCourseNotifier: curso '%s' enviado al chat %s", course.title, chatId)

    def _isInvalidChatError(self, error: ApiTelegramException) -> bool:
        errorText = str(error).lower()
        return (
            error.error_code in (400, 403)
            and (
                "chat not found" in errorText
                or "bot was blocked by the user" in errorText
                or "user is deactivated" in errorText
                or "user not found" in errorText
                or "bot was kicked from the chat" in errorText
                or "bot was kicked from the supergroup chat" in errorText
            )
        )
