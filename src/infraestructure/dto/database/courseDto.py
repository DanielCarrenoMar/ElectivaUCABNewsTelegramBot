from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class CoursesDto(BaseModel):
    id: Optional[int] = None
    source_id: Optional[int] = None
    title: Optional[str] = None
    url: str = None
    uni_countries: Optional[int] = None        # FK countries.id
    disciplinary_fields: Optional[List[int]] = None   # FK disciplinary_fields.id
    course_university: Optional[int] = None    # FK universities.id
    uni_languages: Optional[int] = None        # FK languages.id
    course_levels: Optional[int] = None        # FK course_levels.id
    start_class_date: Optional[date] = None
    end_class_date: Optional[date] = None
    start_inscription_date: Optional[date] = None
    end_inscription_date: Optional[date] = None
    description: Optional[str] = None
    study_hours: Optional[int] = None
    slots: Optional[int] = None
    modified_date: date = None