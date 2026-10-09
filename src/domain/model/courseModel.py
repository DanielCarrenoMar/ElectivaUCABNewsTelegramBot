from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator

DESCRIPTION_MAX_LENGTH = 400

_PENDING = "Por definir"


class CourseRecordDto(BaseModel):
    """Fila plana de la tabla courses del catálogo, con sus catálogos ya resueltos."""

    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    siteUrl: Optional[str] = None
    modality: Optional[str] = None
    credits: Optional[int] = None
    enrollmentStart: Optional[date] = None
    enrollmentEnd: Optional[date] = None
    courseStart: Optional[date] = None
    courseEnd: Optional[date] = None
    totalSeats: Optional[int] = None
    availableSeats: Optional[int] = None
    updatedAt: datetime
    campusName: Optional[str] = None
    universityName: Optional[str] = None
    cityName: Optional[str] = None
    countryIsoCode: Optional[str] = None
    countryName: Optional[str] = None
    languageCode: Optional[str] = None
    languageName: Optional[str] = None
    academicLevelId: Optional[str] = None
    academicLevelName: Optional[str] = None
    sourceName: Optional[str] = None


class CatalogEntry(BaseModel):
    """Valor Natural-key de un catálogo y su etiqueta para mostrar en el teclado de filtros."""

    value: str
    label: str


class ShowCourseModel(BaseModel):
    source: Optional[str] = None
    university: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    disciplinaryFields: Optional[List[str]] = None
    courseLevel: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    startClassDate: Optional[date] = None
    endClassDate: Optional[date] = None
    startInscriptionDate: Optional[date] = None
    endInscriptionDate: Optional[date] = None
    description: Optional[str] = None
    slots: Optional[int] = None       # courses.available_seats
    updatedAt: Optional[datetime] = None

    classDateRange: Optional[str] = None
    inscriptionDateRange: Optional[str] = None

    @field_validator("source", "university", "country", "language", "courseLevel", "title")
    @classmethod
    def _formatText(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value and value.strip() else None

    @field_validator("disciplinaryFields")
    @classmethod
    def _formatTextList(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if not value:
            return None
        cleaned = [item.strip() for item in value if item and item.strip()]
        return cleaned or None

    @field_validator("startClassDate", "endClassDate", "startInscriptionDate", "endInscriptionDate")
    @classmethod
    def _formatDate(cls, value: Optional[date]) -> Optional[str]:
        if value is None or value == date.min:
            return None
        return value.strftime("%Y-%m-%d")

    @field_validator("slots")
    @classmethod
    def _formatNumber(cls, value: Optional[int]) -> Optional[str]:
        if value is None or value == 0:
            return None
        return str(value)

    @field_validator("description")
    @classmethod
    def _formatDescription(cls, value: Optional[str]) -> Optional[str]:
        text = (value or "").strip()
        if not text:
            return None
        if len(text) > DESCRIPTION_MAX_LENGTH:
            return text[:DESCRIPTION_MAX_LENGTH].rstrip() + "…"
        return text

    @model_validator(mode="after")
    def _formatRanges(self) -> "ShowCourseModel":
        def _dateRange(startLabel: Optional[str], endLabel: Optional[str]) -> Optional[str]:
            if startLabel is None and endLabel is None:
                return None
            if startLabel is None:
                return endLabel
            if endLabel is None:
                return startLabel
            return f"{startLabel} - {endLabel}"

        self.classDateRange = _dateRange(self.startClassDate, self.endClassDate)
        self.inscriptionDateRange = _dateRange(self.startInscriptionDate, self.endInscriptionDate)
        return self

    def buildMessage(self) -> str:
        lines = [
            f"<b><a href=\"{self.url}\">{self.title or _PENDING}</a></b>" if self.url else f"<b>{self.title or _PENDING}</b>",
            f"de {self.source}" if self.source else "",
            f"  • 🕒 Fecha de modificación: {self.updatedAt.strftime('%Y-%m-%d') if self.updatedAt else ''}",
            f"  • 🏛️ Universidad: {self.university}" if self.university else "",
            f"  • 🌍 País: {self.country}" if self.country else "",
            f"  • 🗣️ Idioma: {self.language}" if self.language else "",
            f"  • 🧠 Áreas: {', '.join(self.disciplinaryFields)}" if self.disciplinaryFields else "",
            f"  • 📅 Clases: {self.classDateRange}" if self.classDateRange else "",
            f"  • 📝 Inscripción: {self.inscriptionDateRange}" if self.inscriptionDateRange else "",
            f"  • 👥 Cupos: {self.slots}" if self.slots else "",
            "",
            self.description or "",
        ]
        return "\n".join(line for line in lines if line)