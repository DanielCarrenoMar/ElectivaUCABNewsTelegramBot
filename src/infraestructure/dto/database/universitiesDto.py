from typing import Optional
from pydantic import BaseModel


class UniversitiesDto(BaseModel):
    id: Optional[int] = None
    university: Optional[str] = None