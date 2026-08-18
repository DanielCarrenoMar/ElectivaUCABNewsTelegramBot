from datetime import date
from typing import Optional

from pydantic import BaseModel

class AusjalCourseDto(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    documentUrl: Optional[str] = None
    uniCountries: Optional[str] = None
    disciplinaryField: Optional[str] = None
    courseUniversity: Optional[str] = None
    courseLevels: Optional[str] = None
    startClassDate: Optional[date] = None
    endClassDate: Optional[date] = None
    startInscriptionDate: Optional[date] = None
    endInscriptionDate: Optional[date] = None
    study_hours: Optional[int] = None
    slots: Optional[int] = None
    modifiedDate: Optional[date] = None