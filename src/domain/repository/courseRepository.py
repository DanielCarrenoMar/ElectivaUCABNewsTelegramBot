from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from src.infraestructure.dto.database.courseDto import CoursesDto


class CourseFilters(BaseModel):
    keyword: Optional[str] = None
    educationLevel: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    minStudyHours: Optional[int] = None
    university: Optional[str] = None
    minModifiedDate: Optional[date] = None


class CourseRepository(ABC):
    @abstractmethod
    def getCourses(self, filters: CourseFilters) -> List[CoursesDto]:
        raise NotImplementedError