from typing import Optional
from pydantic import BaseModel


class DisciplinaryFieldsDto(BaseModel):
    id: Optional[int] = None
    disciplinary_field: Optional[str] = None