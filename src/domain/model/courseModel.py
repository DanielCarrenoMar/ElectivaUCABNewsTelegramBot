
from datetime import date
from enum import Enum

class EducationLevelEnum(str, Enum):
    UNDERGRADUATE = "undergraduate"
    POSTGRADUATE = "postgraduate"


class CourseModel:
    def __init__(self, title: str, educationLevel: EducationLevelEnum, url: str, university: str, country: str, language: str, startClassDate: date, endClassDate: date, startIncriptionDate: date, endInscriptionDate: date):
        self.title = title
        self.educationLevel = educationLevel
        self.url = url
        self.university = university
        self.country = country
        self.language = language
        self.startClassDate = startClassDate
        self.endClassDate = endClassDate
        self.startIncriptionDate = startIncriptionDate
        self.endInscriptionDate = endInscriptionDate