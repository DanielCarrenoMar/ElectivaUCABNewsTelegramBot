
from datetime import date
from enum import Enum
from pydantic import BaseModel

class EducationLevelEnum(str, Enum):
    UNDERGRADUATE = "undergraduate"
    POSTGRADUATE = "postgraduate"


class CourseModel(BaseModel):
    title: str
    educationLevel: EducationLevelEnum
    univercity: str
    url: str
    country: str
    language: str
    startClassDate: date
    endClassDate: date
    startIncriptionDate: date
    endInscriptionDate: date
    description: str
    studyHours: int
    slots: int
