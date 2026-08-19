from datetime import date
from typing import Optional
from pydantic import BaseModel


class EmoviesWebScraperCourseDto(BaseModel):
    country: Optional[str] = None
    language: Optional[str] = None
    courseLevel: Optional[str] = None
    startClassDate: Optional[date] = None
    endClassDate: Optional[date] = None
    startInscriptionDate: Optional[date] = None
    endInscriptionDate: Optional[date] = None
    description: Optional[str] = None
    studyHours: Optional[int] = None
    slots: Optional[int] = None