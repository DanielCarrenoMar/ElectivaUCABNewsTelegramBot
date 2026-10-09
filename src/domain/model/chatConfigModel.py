from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChatConfig(BaseModel):
    # Los filtros guardan la clave natural del catálogo de cursos, no un id propio:
    # no hay llave foránea entre bases de datos.
    id: int
    isSubscribed: bool = True
    lastRevision: Optional[datetime] = None
    countryIsoCode: Optional[str] = None       # countries.iso_code
    disciplinaryField: Optional[str] = None    # knowledge_areas.name
    courseUniversity: Optional[str] = None     # universities.name
    courseLanguageCode: Optional[str] = None   # languages.code
    courseLevelId: Optional[str] = None        # academic_levels.id
    keyWord: Optional[str] = None