from abc import ABC, abstractmethod

from src.domain.model.courseModel import ShowCourseModel


class InvalidTelegramChatError(Exception):
    def __init__(self, chat_id: int, message: str):
        self.chat_id = chat_id
        super().__init__(message)


class notifierRepository(ABC):
    @abstractmethod
    def sendCourseToChat(self, chatId: int, course: ShowCourseModel) -> None:
        raise NotImplementedError