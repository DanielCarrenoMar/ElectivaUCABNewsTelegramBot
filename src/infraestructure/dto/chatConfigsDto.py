from datetime import date
from typing import Optional
from pydantic import BaseModel


class ChatConfigsDto(BaseModel):
    id: Optional[int] = None
    lastrevision: Optional[date] = None
    uni_countries: Optional[int] = None
    disciplinary_field: Optional[int] = None
    course_university: Optional[int] = None
    uni_languages: Optional[int] = None
    course_levels: Optional[int] = None
    key_word: Optional[str] = None