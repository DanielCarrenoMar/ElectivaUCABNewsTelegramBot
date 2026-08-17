from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from domain.model.chatConfigModel import ChatConfig
from src.domain.model.courseModel import CourseModel
from src.infraestructure.dto.database.courseDto import CoursesDto


class DatabaseCourseFilters(BaseModel):
    country_id: Optional[int] = None
    disciplinary_field_id: Optional[int] = None
    university_id: Optional[int] = None
    language_id: Optional[int] = None
    course_level_id: Optional[int] = None
    keyword: Optional[str] = None
    min_modified_date: Optional[date] = None


class DatabaseRepository(ABC):
    @abstractmethod
    def deleteAllCourses(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def saveCourses(self, courses: List[CoursesDto]) -> int:
        raise NotImplementedError

    @abstractmethod
    def getCourses(self, filters: DatabaseCourseFilters) -> List[CourseModel]:
        raise NotImplementedError

    @abstractmethod
    def getOrCreateChatConfig(self, chatId: int) -> ChatConfig:
        raise NotImplementedError

    @abstractmethod
    def getSubcriptorsChatConfig(self) -> List[ChatConfig]:
        raise NotImplementedError

    @abstractmethod
    def updateChatLastRevision(self, chatId: int, lastRevision: date) -> None:
        raise NotImplementedError

    @abstractmethod
    def updateChatSubscription(self, chatId: int, subscribed: bool) -> None:
        raise NotImplementedError