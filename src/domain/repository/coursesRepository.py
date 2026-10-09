from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List

from src.domain.model.courseModel import CatalogEntry, CourseRecordDto


class CoursesRepository(ABC):
    """Contrato de solo lectura sobre el catálogo de cursos (propiedad de otro sistema)."""

    @abstractmethod
    def getCoursesUpdatedAfter(self, moment: datetime) -> List[CourseRecordDto]:
        """Cursos activos con updated_at estrictamente posterior a moment, del más nuevo al más viejo."""
        raise NotImplementedError

    @abstractmethod
    def getKnowledgeAreasByCourseIds(self, courseIds: List[str]) -> Dict[str, List[str]]:
        """Nombres de las áreas de conocimiento de cada curso, indexados por id de curso."""
        raise NotImplementedError

    @abstractmethod
    def getCountryCatalog(self) -> List[CatalogEntry]:
        """Catálogo de países: valor = iso_code, etiqueta = name."""
        raise NotImplementedError

    @abstractmethod
    def getUniversityCatalog(self) -> List[CatalogEntry]:
        """Catálogo de universidades: valor y etiqueta = name."""
        raise NotImplementedError

    @abstractmethod
    def getLanguageCatalog(self) -> List[CatalogEntry]:
        """Catálogo de idiomas: valor = code, etiqueta = name."""
        raise NotImplementedError

    @abstractmethod
    def getAcademicLevelCatalog(self) -> List[CatalogEntry]:
        """Catálogo de niveles académicos: valor = id, etiqueta = name."""
        raise NotImplementedError

    @abstractmethod
    def getKnowledgeAreaCatalog(self) -> List[CatalogEntry]:
        """Catálogo de áreas de conocimiento: valor y etiqueta = name."""
        raise NotImplementedError