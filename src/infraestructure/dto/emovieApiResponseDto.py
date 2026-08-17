from typing import List, TypedDict


class EmovieApiCourseDto(TypedDict, total=False):
    ID: int
    post_author: str
    post_date: str
    post_date_gmt: str
    comment_status: str
    post_name: str
    post_modified: str
    post_modified_gmt: str
    guid: str
    post_type: str


class EmovieApiCoursesDto(TypedDict, total=False):
    posts: List[EmovieApiCourseDto]
    post_count: int
    found_posts: int
    max_num_pages: int
    max_num_comment_pages: int
    comment_count: int


class EmovieApiDataDto(TypedDict, total=False):
    uni_countries: str
    course_university: str
    uni_languages: str
    disciplinary_field: str
    uni_search: str
    course_levels: str
    course_drafts: str
    course_fields: bool
    courses: EmovieApiCoursesDto
    max_num_page: int
    count: int
    paged: int


class EmovieApiResponseDto(TypedDict, total=False):
    success: bool
    data: EmovieApiDataDto