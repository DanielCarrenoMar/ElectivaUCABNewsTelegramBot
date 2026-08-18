from datetime import date
from enum import Enum
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


def _educationLevelLabel(level: EducationLevelEnum) -> str:
    if level == EducationLevelEnum.POSTGRADUATE:
        return "Posgrado"
    return "Pregrado"


def _truncate(description: str) -> str:
    text = description.strip()
    if not text:
        return _PENDING
    if len(text) > DESCRIPTION_MAX_LENGTH:
        return text[:DESCRIPTION_MAX_LENGTH].rstrip() + "…"
    return text


class EducationLevelEnum(str, Enum):
    UNDERGRADUATE = "undergraduate"
    POSTGRADUATE = "postgraduate"


class CourseModel(BaseModel):
    externalId: Optional[int] = None
    title: str
    educationLevel: EducationLevelEnum
    university: str
    url: str
    country: str
    language: str
    startClassDate: date
    endClassDate: date
    startInscriptionDate: date
    endInscriptionDate: date
    description: str
    studyHours: int
    slots: int
    modifiedDate: date = date.min

    def buildMessage(self) -> str:
        lines = [
            f"<b>{self.title or _PENDING}</b>",
            f"🔗 <a href=\"{self.url}\">Ver curso</a>" if self.url else "",
            f"🏛️ Universidad: {_textOrPending(self.university)}",
            f"🌍 País: {_textOrPending(self.country)}",
            f"🗣️ Idioma: {_textOrPending(self.language)}",
            f"🎓 Nivel: {_educationLevelLabel(self.educationLevel)}",
            f"📅 Clases: {_dateRange(self.startClassDate, self.endClassDate)}",
            f"📝 Inscripción: {_dateRange(self.startInscriptionDate, self.endInscriptionDate)}",
            f"⏱️ Horas de estudio: {_numberOrPending(self.studyHours)}",
            f"👥 Cupos: {_numberOrPending(self.slots)}",
            "",
            _truncate(self.description),
        ]
        return "\n".join(line for line in lines if line)