import logging

from src.domain.repository.notifierRepository import notifierRepository
from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


class SendCourseToSubcriptorsUseCase:
    def __init__(self, notifier: notifierRepository):
        self._databaseRepository = PostgresDatabaseRepositoryImp()
        self._notifier = notifier

    def execute(self) -> int:
        totalSent = 0
        chatConfigs = self._databaseRepository.getSubcriptorsChatConfig()
        logging.info("SendCourseToSubcriptorsUseCase: procesando %d configuraciones de chat", len(chatConfigs))

        matches = self._databaseRepository.getNewCoursesForChats()
        coursesByChatId = {match.chatId: match.courses for match in matches}

        for chat in chatConfigs:
            courses = coursesByChatId.get(chat.id)
            if courses is None:
                logging.debug(
                    "SendCourseToSubcriptorsUseCase: sin cursos para el chat %s; no se actualiza lastrevision",
                    chat.id,
                )
                continue

            try:
                sent = 0
                for course in courses:
                    self._notifier.sendCourseToChat(chat.id, course)
                    sent += 1

                chat.lastRevision = courses[0].modifiedDate
                self._databaseRepository.updateChatConfig(chat)
                totalSent += sent

                logging.info(
                    "SendCourseToSubcriptorsUseCase: el chat %s recibió %d curso(s); lastrevision actualizada a %s",
                    chat.id,
                    sent,
                    courses[0].modifiedDate,
                )
            except Exception:
                logging.exception("SendCourseToSubcriptorsUseCase: error procesando el chat %s", chat.id)

        logging.info("SendCourseToSubcriptorsUseCase: total de cursos enviados %d", totalSent)
        return totalSent
