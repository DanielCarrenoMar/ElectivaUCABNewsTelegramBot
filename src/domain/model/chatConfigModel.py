from datetime import date
from typing import Optional

from pydantic import BaseModel


class ChatConfig(BaseModel):
    id: int
    isSubscribed: bool = True
    lastRevision: Optional[date] = None
    uniCountries: Optional[int] = None          # FK countries.id
    disciplinaryField: Optional[int] = None     # FK disciplinary_fields.id
    courseUniversity: Optional[int] = None      # FK universities.id
    uniLanguages: Optional[int] = None          # FK languages.id
    courseLevels: Optional[int] = None          # FK course_levels.id
    keyWord: Optional[str] = None