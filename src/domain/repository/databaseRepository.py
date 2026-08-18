from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from src.domain.model.chatConfigModel import ChatConfig
from src.domain.model.courseModel import CourseModel
from src.infraestructure.dto.database.courseDto import CoursesDto


class DatabaseCourseFilters(BaseModel):
    countryId: Optional[int] = None
    disciplinaryFieldId: Optional[int] = None
    universityId: Optional[int] = None
    languageId: Optional[int] = None
    courseLevelId: Optional[int] = None
    keyword: Optional[str] = None
    minModifiedDate: Optional[date] = None


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