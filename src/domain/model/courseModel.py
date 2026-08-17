from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel

class EducationLevelEnum(str, Enum):
    UNDERGRADUATE = "undergraduate"
    POSTGRADUATE = "postgraduate"


class CourseModel(BaseModel):
    externalId: Optional[int] = None
    title: str
    educationLevel: EducationLevelEnum
    university: str
    url: str
    country: str
    language: str
    startClassDate: date
    endClassDate: date
    startInscriptionDate: date
    endInscriptionDate: date
    description: str
    studyHours: int
    slots: int
    modifiedDate: date = date.min