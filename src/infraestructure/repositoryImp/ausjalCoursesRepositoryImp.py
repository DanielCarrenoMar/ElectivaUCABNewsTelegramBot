import logging
import re
from datetime import date, datetime
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from src.domain.model.courseModel import CourseModel
from src.domain.repository.courseRepository import CourseFilters, CourseSourceRepository
from src.infraestructure.dto.ausjal.ausjalCourseDto import AusjalCourseDto
from src.infraestructure.mapper.ausjal.ausjalMapper import ausjalCourseDtoToCourseModel

_SPANISH_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

_ALL_DATES_REGEX = re.compile(
    r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{1,2}\s+de\s+[A-Za-záéíóúñü]+(?:\s+(?:de|del)\s+)?\d{4}\b",
    re.IGNORECASE,
)

logger = logging.getLogger("AusjalSourceRepositoryImp")

class AusjalSourceRepositoryImp(CourseSourceRepository):
    SOURCE_URL = "https://cursos.iberoleon.mx/intercambiovirtual/index-icv.php"
    REQUEST_TIMEOUT_SECONDS = 30

    def getCourses(self, filters: CourseFilters) -> List[CourseModel]:
        response = requests.get(self.SOURCE_URL, timeout=self.REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()

        courseDtos = self.extractCourses(response.text)
        courses: List[CourseModel] = []

        for courseDto in courseDtos:
            courseModel = ausjalCourseDtoToCourseModel(courseDto)

            if filters.minStudyHours is not None and courseModel.studyHours < filters.minStudyHours:
                logger.debug(
                    "Curso '%s' descartado: studyHours %d < minStudyHours %d",
                    courseModel.title,
                    courseModel.studyHours,
                    filters.minStudyHours,
                )
                continue

            if filters.keyword is not None and filters.keyword.lower() not in courseModel.title.lower():
                logger.debug(
                    "Curso '%s' descartado: no contiene keyword '%s'",
                    courseModel.title,
                    filters.keyword,
                )
                continue

            if filters.minModifiedDate is not None and courseModel.modifiedDate < filters.minModifiedDate:
                logger.debug(
                    "Curso '%s' descartado: modifiedDate %s < minModifiedDate %s",
                    courseModel.title,
                    courseModel.modifiedDate,
                    filters.minModifiedDate,
                )
                continue

            courses.append(courseModel)

        logger.info("getCourses devolvió %d cursos de AUSJAL", len(courses))
        return courses

    def extractCourses(self, html: str) -> List[AusjalCourseDto]:
        soup = BeautifulSoup(html, "html.parser")
        courses: List[AusjalCourseDto] = []

        for countryItem in soup.select("div.accordion-item", limit=5):
            countryHeader = countryItem.find("h4")
            uni_countries = countryHeader.get_text(strip=True) if countryHeader else None

            for uniCard in countryItem.select("div.card.card-body.accordion-item"):
                universityHeader = uniCard.find("h5")
                course_university = None
                if universityHeader is not None:
                    universityButton = universityHeader.find("button")
                    if universityButton is not None:
                        course_university = universityButton.get_text(strip=True)

                for table in uniCard.find_all("table"):
                    headers = [th.get_text(strip=True) for th in table.select("thead th")]
                    header_index = {name: idx for idx, name in enumerate(headers)}

                    for row in table.select("tbody tr"):
                        cells = row.find_all("td")

                        def _cell(name: str):
                            idx = header_index.get(name)
                            if idx is None or idx >= len(cells):
                                return None
                            return cells[idx]

                        courseLevelCell = _cell("Tipo")
                        titleCell = _cell("Materia")
                        disciplinaryFieldCell = _cell("Campo profesional")
                        inscriptionCell = _cell("Fecha(s) de inscripción")
                        startClassCell = _cell("Inicio de clase")
                        endClassCell = _cell("Fin de curso")
                        studyHoursCell = _cell("Horas de estudio aprox. por semana")
                        slotsCell = _cell("Cupo")
                        detailCell = _cell("Detalle de la materia")

                        start_inscription_date, end_inscription_date = self._parseInscriptionDates(
                            inscriptionCell.get_text(strip=True) if inscriptionCell else None
                        )

                        studyHoursText = studyHoursCell.get_text(strip=True) if studyHoursCell else ""
                        studyHoursMatch = re.match(r"\d+", studyHoursText)
                        study_hours = int(studyHoursMatch.group(0)) if studyHoursMatch else None

                        slotsText = slotsCell.get_text(strip=True) if slotsCell else ""
                        slots = int(slotsText) if slotsText.isdigit() else None

                        documentUrl = None
                        if detailCell is not None:
                            link = detailCell.find("a")
                            if link is not None and "href" in link.attrs:
                                documentUrl = link["href"]

                        modified_date = None
                        if documentUrl:
                            try:
                                response = requests.head(documentUrl, allow_redirects=True, timeout=5)
                                last_modified = response.headers.get("Last-Modified")

                                if last_modified:
                                    modified_date = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %z").date()
                            except Exception:
                                pass

                        startClassDate = self._parseDate(startClassCell.get_text(strip=True) if startClassCell else None)

                        if not modified_date:
                            modified_date = startClassDate or date.today()

                        courses.append(
                            AusjalCourseDto(
                                title=titleCell.get_text(strip=True) if titleCell else None,
                                courseLevels=courseLevelCell.get_text(strip=True) if courseLevelCell else None,
                                url="https://intercampusausjal.com/asignaturas-virtuales/",
                                documentUrl=documentUrl,
                                uniCountries=uni_countries,
                                disciplinaryField=disciplinaryFieldCell.get_text(strip=True)
                                if disciplinaryFieldCell
                                else None,
                                courseUniversity=course_university,
                                startClassDate=startClassDate,
                                endClassDate=self._parseDate(
                                    endClassCell.get_text(strip=True) if endClassCell else None
                                ),
                                startInscriptionDate=start_inscription_date,
                                endInscriptionDate=end_inscription_date,
                                study_hours=study_hours,
                                slots=slots,
                                modifiedDate=modified_date,
                            )
                        )

        return courses

    def _parseDate(self, date_string: Optional[str]) -> Optional[date]:
        if not date_string:
            logger.debug("No se proporcionó una cadena de fecha para analizar.")
            return None

        text = date_string.strip()
        numericMatch = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
        if numericMatch:
            day, month, year = numericMatch.groups()
            try:
                return date(int(year), int(month), int(day))
            except ValueError:
                logger.warning("Error al crear la fecha a partir de los valores: day=%s, month=%s, year=%s", day, month, year)
                return None

        spanishMatch = re.fullmatch(
            r"(\d{1,2})\s+de\s+([A-Za-záéíóúñü]+)(?:\s+(?:de|del)\s+)?(\d{4})",
            text,
            re.IGNORECASE,
        )
        if spanishMatch:
            day = int(spanishMatch.group(1))
            month = _SPANISH_MONTHS.get(spanishMatch.group(2).lower())
            year = int(spanishMatch.group(3))
            if month is None:
                logger.warning("Mes no válido: %s", spanishMatch.group(2))
                return None
            try:
                return date(year, month, day)
            except ValueError:
                logger.warning("Error al crear la fecha a partir de los valores: day=%d, month=%s, year=%d", day, month, year)
                return None

        return None

    def _parseInscriptionDates(self, text: Optional[str]) -> tuple[Optional[date], Optional[date]]:
        if not text or not text.strip():
            return None, None

        dateMatches = _ALL_DATES_REGEX.findall(text)
        parsedDates = [parsed for match in dateMatches if (parsed := self._parseDate(match)) is not None]

        start_date = parsedDates[0] if len(parsedDates) > 0 else None
        end_date = parsedDates[1] if len(parsedDates) > 1 else None
        return start_date, end_date