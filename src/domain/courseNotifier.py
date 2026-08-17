from abc import ABC, abstractmethod

from src.domain.model.courseModel import CourseModel


class CourseNotifier(ABC):
    @abstractmethod
    def sendCourseToChat(self, chatId: int, course: CourseModel) -> None:
        raise NotImplementedError