from typing import Optional
from pydantic import BaseModel


class LanguagesDto(BaseModel):
    id: Optional[int] = None
    language: Optional[str] = None