import logging
from datetime import date
from typing import Optional

from telebot import TeleBot

from src.domain.model.courseModel import CourseModel, EducationLevelEnum
from src.domain.courseNotifier import CourseNotifier

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


class TelegramCourseNotifier(CourseNotifier):
    def __init__(self, bot: TeleBot):
        self._bot = bot

    def sendCourseToChat(self, chatId: int, course: CourseModel) -> None:
        text = self._buildMessage(course)
        self._bot.send_message(
            chatId,
            text,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        logging.info("TelegramCourseNotifier: curso '%s' enviado al chat %s", course.title, chatId)

    def _buildMessage(self, course: CourseModel) -> str:
        lines = [
            f"<b>{course.title or _PENDING}</b>",
            f"🔗 <a href=\"{course.url}\">Ver curso</a>" if course.url else "",
            f"🏛️ Universidad: {_textOrPending(course.university)}",
            f"🌍 País: {_textOrPending(course.country)}",
            f"🗣️ Idioma: {_textOrPending(course.language)}",
            f"🎓 Nivel: {_educationLevelLabel(course.educationLevel)}",
            f"📅 Clases: {_dateRange(course.startClassDate, course.endClassDate)}",
            f"📝 Inscripción: {_dateRange(course.startInscriptionDate, course.endInscriptionDate)}",
            f"⏱️ Horas de estudio: {_numberOrPending(course.studyHours)}",
            f"👥 Cupos: {_numberOrPending(course.slots)}",
            "",
            _truncate(course.description),
        ]
        return "\n".join(line for line in lines if line)