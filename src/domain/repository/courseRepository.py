from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from src.domain.model.courseModel import CourseModel


class CourseFilters(BaseModel):
    keyword: Optional[str] = None
    educationLevel: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    disciplinaryField: Optional[str] = None
    minStudyHours: Optional[int] = None
    university: Optional[str] = None
    minModifiedDate: Optional[date] = None


class CourseSourceRepository(ABC):
    @abstractmethod
    def getCourses(self, filters: CourseFilters) -> List[CourseModel]:
        raise NotImplementedError