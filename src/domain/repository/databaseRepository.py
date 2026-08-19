from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from src.domain.model.chatConfigModel import ChatConfig
from src.domain.model.courseModel import ShowCourseModel
from src.infraestructure.dto.database.courseDto import CoursesDto


class DatabaseCourseFilters(BaseModel):
    countryId: Optional[int] = None
    disciplinaryFieldId: Optional[int] = None
    universityId: Optional[int] = None
    languageId: Optional[int] = None
    courseLevelId: Optional[int] = None
    keyword: Optional[str] = None
    minModifiedDate: Optional[date] = None


class ChatNewCourses(BaseModel):
    chatId: int
    courses: List[ShowCourseModel]


class DatabaseRepository(ABC):
    @abstractmethod
    def deleteAllCourses(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def saveCourses(self, courses: List[CoursesDto]) -> int:
        raise NotImplementedError

    @abstractmethod
    def getCourses(self, filters: DatabaseCourseFilters) -> List[ShowCourseModel]:
        raise NotImplementedError

    @abstractmethod
    def getOrCreateChatConfig(self, chatId: int) -> ChatConfig:
        raise NotImplementedError

    @abstractmethod
    def getSubcriptorsChatConfig(self) -> List[ChatConfig]:
        raise NotImplementedError

    @abstractmethod
    def getNewCoursesForChats(self) -> List[ChatNewCourses]:
        raise NotImplementedError

    @abstractmethod
    def updateChatConfig(self, chatConfig: ChatConfig) -> None:
        raise NotImplementedError