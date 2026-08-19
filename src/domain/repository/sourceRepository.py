from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from src.domain.model.courseModel import CourseModel


class CourseFilters(BaseModel):
    keyword: Optional[str] = None
    courseLevel: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    disciplinaryField: Optional[str] = None
    minStudyHours: Optional[int] = None
    university: Optional[str] = None
    minModifiedDate: Optional[date] = None


class SourceRepository(ABC):
    # Identificador de la fuente en courses_sources; cada implementación define el suyo
    # (ver APP_COURSE_SOURCES en src/config/defaultValuesCatalog.py).
    SOURCE_ID: int = 0

    @abstractmethod
    def getCourses(self, filters: CourseFilters, max: Optional[int] = None) -> List[CourseModel]:
        raise NotImplementedError