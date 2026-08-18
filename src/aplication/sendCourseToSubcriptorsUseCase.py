import logging

from src.domain.model.chatConfigModel import ChatConfig
from src.domain.repository.notifierRepository import notifierRepository
from src.domain.repository.databaseRepository import DatabaseCourseFilters
from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


class SendCourseToSubcriptorsUseCase:
    def __init__(self, notifier: notifierRepository):
        self._databaseRepository = PostgresDatabaseRepositoryImp()
        self._notifier = notifier

    def execute(self) -> int:
        totalSent = 0
        chatConfigs = self._databaseRepository.getSubcriptorsChatConfig()
        logging.info("SendCourseToSubcriptorsUseCase: procesando %d configuraciones de chat", len(chatConfigs))

        for chat in chatConfigs:
            try:
                totalSent += self._processChat(chat)
            except Exception:
                logging.exception("SendCourseToSubcriptorsUseCase: error procesando el chat %s", chat.id)

        logging.info("SendCourseToSubcriptorsUseCase: total de cursos enviados %d", totalSent)
        return totalSent

    def _processChat(self, chat: ChatConfig) -> int:

        filters = DatabaseCourseFilters(
            countryId=chat.uniCountries,
            disciplinaryFieldId=chat.disciplinaryField,
            universityId=chat.courseUniversity,
            languageId=chat.uniLanguages,
            courseLevelId=chat.courseLevels,
            keyword=chat.keyWord,
            minModifiedDate=chat.lastRevision,
        )
        courses = self._databaseRepository.getCourses(filters)
        if not courses:
            logging.debug(
                "SendCourseToSubcriptorsUseCase: sin cursos para el chat %s; no se actualiza lastrevision",
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
            "SendCourseToSubcriptorsUseCase: el chat %s recibió %d curso(s); lastrevision actualizada a %s",
            chat.id,
            sent,
            newest,
        )
        return sent