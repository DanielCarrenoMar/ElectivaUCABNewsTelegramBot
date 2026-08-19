from datetime import date, datetime
from pathlib import Path
from typing import Optional, Union

from src.domain.model.courseModel import CourseModel
from src.infraestructure.dto.emovies.emovieApiResponseDto import EmovieApiCourseDto, EmovieApiDataDto
from src.infraestructure.dto.emovies.emovieswebScraperCourseDto import EmoviesWebScraperCourseDto
from src.infraestructure.mapper.emovies.emoviesCatalogTranslator import emoviesIdCatalogToAppIdCatalog
from src.infraestructure.mapper.emovies.emoviesHtmlTagTraductor import emoviesHtmlTagToAppIdCatalog

from bs4 import BeautifulSoup

COURSE_URL_BASE = "https://emovies.oui-iohe.org/nuestros-cursos/"

def parseApiDatetime(value: Optional[str]) -> Optional[date]:
    """Convierte una fecha de la API ('2026-05-12 09:14:21' o ISO) a date."""
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _courseUrl(apiCourseDto: EmovieApiCourseDto) -> str:
    slug = apiCourseDto.post_name or ""
    if slug:
        return f"{COURSE_URL_BASE}{slug}"
    return apiCourseDto.guid or ""

def _courseModifiedDate(apiCourseDto: EmovieApiCourseDto) -> date:
    parsedDates = [
        parsedDate
        for parsedDate in (
            parseApiDatetime(apiCourseDto.post_date),
            parseApiDatetime(apiCourseDto.post_modified),
        )
        if parsedDate is not None
    ]

    if not parsedDates:
        return date.min

    return max(parsedDates)

def _extractHtmlData(html:str):
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.find_all("div", class_="item--course")
    
    cardsInfo = []

    for card in cards:
        cardClassz = card.get("class", [])

        disciplinaryTags = []
        level = ""
        language = ""

        for cardClass in cardClassz:
            if cardClass.startswith("course_disciplinary_new"):
                disciplinaryTags.append("-".join(cardClass.split("-")[1:]))
            elif cardClass.startswith("course_level"):
                level = "-".join(cardClass.split("-")[1:])
            elif cardClass.startswith("university_language"):
                language = "-".join(cardClass.split("-")[1:])

        cardsInfo.append((disciplinaryTags, level, language))

    return cardsInfo


def emovieResponseToCourseModels(
    apiDataDto: EmovieApiDataDto,
    webScraperCourseDto: Optional[EmoviesWebScraperCourseDto],
) -> list[CourseModel]:
    detail = webScraperCourseDto or EmoviesWebScraperCourseDto()

    courseModels: list[CourseModel] = [
        CourseModel(
            sourceId=1,  # id de Emovies
            title=course.post_title,
            url=_courseUrl(course),
            modifiedDate=_courseModifiedDate(course),
        )
        for course in apiDataDto.courses.posts
    ]

    for i, (disciplinaryTags, level, language) in enumerate(_extractHtmlData(apiDataDto.courses_html)):
        if i >= len(courseModels):
            break
        disciplinaryIds = [
            appId
            for appId in (
                emoviesHtmlTagToAppIdCatalog("disciplinary_fields", tag)
                for tag in disciplinaryTags
            )
            if appId is not None
        ]
        courseModels[i] = courseModels[i].model_copy(
            update={
                "disciplinaryFields": list(dict.fromkeys(disciplinaryIds)) or None,
                "courseLevel": emoviesHtmlTagToAppIdCatalog("course_levels", level),
                "language": emoviesHtmlTagToAppIdCatalog("languages", language),
            }
        )

    return courseModels
