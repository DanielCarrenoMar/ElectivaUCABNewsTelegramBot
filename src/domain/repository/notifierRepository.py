from abc import ABC, abstractmethod

from src.domain.model.courseModel import ShowCourseModel


class notifierRepository(ABC):
    @abstractmethod
    def sendCourseToChat(self, chatId: int, course: ShowCourseModel) -> None:
        raise NotImplementedError