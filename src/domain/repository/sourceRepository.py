from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.model.courseModel import CourseModel


class SourceRepository(ABC):
    # Identificador de la fuente en courses_sources; cada implementación define el suyo
    # (ver APP_COURSE_SOURCES en src/config/defaultValuesCatalog.py).
    SOURCE_ID: int = 0

    @abstractmethod
    def getCourses(self, max: Optional[int] = None) -> List[CourseModel]:
        raise NotImplementedError