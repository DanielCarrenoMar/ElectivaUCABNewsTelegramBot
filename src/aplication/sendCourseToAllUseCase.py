import logging

from src.domain.model.chatConfigModel import ChatConfig
from src.domain.repository.notifierRepository import notifierRepository
from src.domain.repository.databaseRepository import DatabaseCourseFilters, DatabaseRepository


class SendCourseToAllUseCase:
    def __init__(self, databaseRepository: DatabaseRepository, notifier: notifierRepository):
        self._databaseRepository = databaseRepository
        self._notifier = notifier

    def execute(self) -> int:
        totalSent = 0
        chatConfigs = self._databaseRepository.getSubcriptorsChatConfig()
        logging.info("SendCourseToAllUseCase: procesando %d configuraciones de chat", len(chatConfigs))

        for chat in chatConfigs:
            try:
                totalSent += self._processChat(chat)
            except Exception:
                logging.exception("SendCourseToAllUseCase: error procesando el chat %s", chat.id)

        logging.info("SendCourseToAllUseCase: total de cursos enviados %d", totalSent)
        return totalSent

    def _processChat(self, chat: ChatConfig) -> int:

        filters = DatabaseCourseFilters(
            country_id=chat.uniCountries,
            disciplinary_field_id=chat.disciplinaryField,
            university_id=chat.courseUniversity,
            language_id=chat.uniLanguages,
            course_level_id=chat.courseLevels,
            keyword=chat.keyWord,
            min_modified_date=chat.lastRevision,
        )
        courses = self._databaseRepository.getCourses(filters)
        if not courses:
            logging.debug(
                "SendCourseToAllUseCase: sin cursos para el chat %s; no se actualiza lastrevision",
                chat.id,
            )
            return 0

        newest = courses[0].modifiedDate
        if chat.lastRevision is not None:
            new_courses = [course for course in courses if course.modifiedDate > chat.lastRevision]
        else:
            new_courses = courses

        sent = 0
        for course in new_courses:
            self._notifier.sendCourseToChat(chat.id, course)
            sent += 1

        self._databaseRepository.updateChatLastRevision(chat.id, newest)

        logging.info(
            "SendCourseToAllUseCase: el chat %s recibió %d curso(s); lastrevision actualizada a %s",
            chat.id,
            sent,
            newest,
        )
        return sent