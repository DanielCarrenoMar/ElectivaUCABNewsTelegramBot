from typing import Optional
from pydantic import BaseModel


class EmovieApiParamsDto(BaseModel):
    action: str = "get_courses"
    uni_search: Optional[str] = None
    course_levels: Optional[str] = None
    uni_countries: Optional[str] = None
    uni_languages: Optional[str] = None
    course_university: Optional[str] = None