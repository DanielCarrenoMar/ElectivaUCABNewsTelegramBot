from typing import List, Optional, Union
from pydantic import BaseModel


class EmovieApiCourseDto(BaseModel):
    ID: Optional[int] = None
    post_author: Optional[str] = None
    post_date: Optional[str] = None
    post_date_gmt: Optional[str] = None
    comment_status: Optional[str] = None
    post_name: Optional[str] = None
    post_content: Optional[str] = None
    post_modified: Optional[str] = None
    post_modified_gmt: Optional[str] = None
    guid: Optional[str] = None
    post_type: Optional[str] = None


class EmovieApiCoursesDto(BaseModel):
    posts: Optional[List[EmovieApiCourseDto]] = None
    post_count: Optional[int] = None
    found_posts: Optional[int] = None
    max_num_pages: Optional[int] = None
    max_num_comment_pages: Optional[int] = None
    comment_count: Optional[int] = None


class EmovieApiDataDto(BaseModel):
    uni_countries: Optional[str] = None
    course_university: Optional[str] = None
    uni_languages: Optional[str] = None
    disciplinary_field: Optional[Union[str, bool]] = None
    uni_search: Optional[str] = None
    course_levels: Optional[str] = None
    course_drafts: Optional[Union[str, bool]] = None
    course_fields: Optional[bool] = None
    courses: Optional[EmovieApiCoursesDto] = None
    max_num_page: Optional[int] = None
    count: Optional[int] = None
    paged: Optional[int] = None
    courses_html: str


class EmovieApiResponseDto(BaseModel):
    success: Optional[bool] = None
    data: Optional[EmovieApiDataDto] = None