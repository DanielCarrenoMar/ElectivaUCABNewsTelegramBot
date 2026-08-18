from datetime import date
from typing import Optional

from pydantic import BaseModel

DESCRIPTION_MAX_LENGTH = 400

_PENDING = "Por definir"


def _textOrPending(value: str) -> str:
    return value.strip() if value and value.strip() else _PENDING


def _dateOrPending(value: Optional[date]) -> str:
    if value is None or value == date.min:
        return _PENDING
    return value.strftime("%Y-%m-%d")


def _numberOrPending(value: Optional[int]) -> str:
    if value is None or value == 0:
        return _PENDING
    return str(value)


def _dateRange(start: Optional[date], end: Optional[date]) -> str:
    startLabel = _dateOrPending(start)
    endLabel = _dateOrPending(end)
    if startLabel == _PENDING and endLabel == _PENDING:
        return _PENDING
    return f"{startLabel} - {endLabel}"


def _truncate(description: Optional[str]) -> str:
    text = (description or "").strip()
    if not text:
        return _PENDING
    if len(text) > DESCRIPTION_MAX_LENGTH:
        return text[:DESCRIPTION_MAX_LENGTH].rstrip() + "…"
    return text


class CourseModel(BaseModel):
    sourceId: int = None
    title: Optional[str] = None
    courseLevel: Optional[int] = None
    university: Optional[int] = None
    url: str = None
    country: Optional[int] = None
    language: Optional[int] = None
    disciplinaryField: Optional[int] = None
    startClassDate: Optional[date] = None
    endClassDate: Optional[date] = None
    startInscriptionDate: Optional[date] = None
    endInscriptionDate: Optional[date] = None
    description: Optional[str] = None
    studyHours: Optional[int] = None
    slots: Optional[int] = None
    modifiedDate: date


class ShowCourseModel(BaseModel):
    source: Optional[str] = None
    university: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    disciplinaryField: Optional[str] = None
    courseLevel: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    startClassDate: Optional[date] = None
    endClassDate: Optional[date] = None
    startInscriptionDate: Optional[date] = None
    endInscriptionDate: Optional[date] = None
    description: Optional[str] = None
    studyHours: Optional[int] = None
    slots: Optional[int] = None
    modifiedDate: Optional[date] = None

    def buildMessage(self) -> str:
        lines = [
            f"<b>{self.title or _PENDING}</b>",
            f"🔗 <a href=\"{self.url}\">Ver curso</a>" if self.url else "",
            f"🏛️ Universidad: {_textOrPending(self.university)}",
            f"🌍 País: {_textOrPending(self.country)}",
            f"🗣️ Idioma: {_textOrPending(self.language)}",
            f"📅 Clases: {_dateRange(self.startClassDate, self.endClassDate)}",
            f"📝 Inscripción: {_dateRange(self.startInscriptionDate, self.endInscriptionDate)}",
            f"⏱️ Horas de estudio: {_numberOrPending(self.studyHours)}",
            f"👥 Cupos: {_numberOrPending(self.slots)}",
            "",
            _truncate(self.description),
        ]
        return "\n".join(line for line in lines if line)