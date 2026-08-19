from typing import Optional
from pydantic import BaseModel


class CourseLevelsDto(BaseModel):
    id: Optional[int] = None
    course_level: Optional[str] = None