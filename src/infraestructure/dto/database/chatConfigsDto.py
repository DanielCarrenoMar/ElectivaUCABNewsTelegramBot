from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChatConfigsDto(BaseModel):
    """Fila de chatconfigs: la suscripcion del chat y sus filtros.

    Cada filtro guarda la clave natural del catalogo de cursos (propiedad de otro
    sistema), por eso son texto y no enteros con llave foranea.
    """

    id: Optional[int] = None
    is_subscribed: Optional[bool] = True
    last_revision: Optional[datetime] = None    # courses.updated_at es timestamp
    country_iso_code: Optional[str] = None      # countries.iso_code
    course_university: Optional[str] = None     # universities.name
    course_language_code: Optional[str] = None  # languages.code
    course_level_id: Optional[str] = None       # academic_levels.id
    disciplinary_field: Optional[str] = None    # knowledge_areas.name
    key_word: Optional[str] = None