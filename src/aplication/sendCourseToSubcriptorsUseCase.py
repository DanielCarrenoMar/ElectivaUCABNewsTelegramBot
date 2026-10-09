import logging
from datetime import datetime, timezone
from typing import List, Optional, Sequence

from src.domain.model.chatConfigModel import ChatConfig
from src.domain.model.courseModel import CourseRecordDto, ShowCourseModel
from src.domain.repository.coursesRepository import CoursesRepository
from src.domain.repository.notifierRepository import InvalidTelegramChatError, notifierRepository
from src.infraestructure.mapper.courseRecordMapper import courseRecordToShowCourseModel
from src.infraestructure.repositoryImp.coursesRepositoryImp import CoursesRepositoryImp
from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


def _asUtc(moment: datetime) -> datetime:
    """Normaliza a UTC para poder comparar momentos que vienen de dos bases distintas.

    courses.updated_at es `timestamp without time zone` y llega sin zona horaria,
    mientras que chatconfigs.lastrevision es `timestamptz` y llega con ella. Las dos
    bases están en GMT, asi que leer el valor sin zona como UTC es laconversion
    correcta; sin esto la comparación de frescura lanza TypeError y ningun chat
    recibe nada. El mismo casteo cubre el caso de que el otro sistema pase a
    escribir updated_at con zona.
    """
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment


def courseMatchesChat(
    record: CourseRecordDto,
    knowledgeAreas: Sequence[str],
    chat: ChatConfig,
) -> bool:
    """Dice si un curso es nuevo para un chat segun los filtros de ese chat.

    Es una funcion pura y sin efectos: recibe el registro del catalogo, sus areas de
    conocimiento y la configuracion del chat, y devuelve el veredicto. Se puede
    ejercitar con fixtures sin base de datos.

    Reglas, en el mismo orden en que las evaluaba el SQL de antes:
    - Frescura: updated_at tiene que ser estrictamente posterior a lastrevision.
      Un chat sin lastrevision no tiene nada nuevo que recibir.
    - Un filtro ausente (None) significa "cualquiera".
    - El area disciplinaria coincide con CUALQUIERA de las areas del curso, igual que
      el EXISTS de la consulta anterior.
    - La palabra clave se busca sin distinguir mayusculas en el titulo o en la
      descripcion, como el ILIKE '%' || TRIM(key_word) || '%' de antes.
    - Un curso sin pais (51% del catalogo: su campus no tiene ciudad) NO puede
      satisfacer un filtro de pais. Resolverlo como "cualquiera" lo dejaria pasar.
    """
    if chat.lastRevision is None or record.updatedAt is None:
        return False
    if _asUtc(record.updatedAt) <= _asUtc(chat.lastRevision):
        return False

    if chat.countryIsoCode is not None and record.countryIsoCode != chat.countryIsoCode:
        return False

    if chat.courseUniversity is not None and record.universityName != chat.courseUniversity:
        return False

    if chat.courseLanguageCode is not None and record.languageCode != chat.courseLanguageCode:
        return False

    if chat.courseLevelId is not None and record.academicLevelId != chat.courseLevelId:
        return False

    if chat.disciplinaryField is not None and chat.disciplinaryField not in knowledgeAreas:
        return False

    if chat.keyWord is not None:
        needle = chat.keyWord.strip().casefold()
        if needle:
            haystacks = (record.title, record.description)
            if not any(text and needle in text.casefold() for text in haystacks):
                return False

    return True


def nextWatermark(
    current: Optional[datetime], maxUpdatedAt: Optional[datetime]
) -> Optional[datetime]:
    """Marca de agua siguiente: la del maximo de candidatos, y jamas retrocede.

    Si el maximo de los candidatos ya es anterior a la marca actual, se devuelve la
    actual. Asi una corrida con pocos candidatos, o un reloj de la otra base que se
    atrasa, nunca hace volver a recorrer el historial.
    """
    if maxUpdatedAt is None:
        return current
    if current is None:
        return maxUpdatedAt
    return maxUpdatedAt if maxUpdatedAt > current else current


class SendCourseToSubcriptorsUseCase:
    def __init__(
        self,
        notifier: notifierRepository,
        onInvalidChat=None,
        coursesRepository: Optional[CoursesRepository] = None,
    ):
        self._databaseRepository = PostgresDatabaseRepositoryImp()
        self._coursesRepository = coursesRepository or CoursesRepositoryImp()
        self._notifier = notifier
        self._onInvalidChat = onInvalidChat

    def execute(self) -> int:
        totalSent = 0
        chatConfigs = self._databaseRepository.getSubcriptorsChatConfig()
        logging.info("SendCourseToSubcriptorsUseCase: procesando %d configuraciones de chat", len(chatConfigs))

        # Un chat sin lastrevision no tiene nada pendiente que recibir, asi que se
        # omite. Tampoco cuenta para el minimo: usarlo como cota de la consulta
        # traeria el historico completo del catalogo para todos los demas.
        pendingChats = [chat for chat in chatConfigs if chat.lastRevision is not None]
        for chat in chatConfigs:
            if chat.lastRevision is None:
                logging.info(
                    "SendCourseToSubcriptorsUseCase: el chat %s no tiene lastrevision; se omite",
                    chat.id,
                )
        if not pendingChats:
            logging.info("SendCourseToSubcriptorsUseCase: ningún chat suscrito tiene lastrevision; no hay nada que enviar")
            return 0

        # Los candidatos se traen una sola vez para todos los chats: el predicado de
        # fecha baja a SQL y el resto de los filtros se evalua en Python.
        minRevision = min(_asUtc(chat.lastRevision) for chat in pendingChats)
        candidates = self._coursesRepository.getCoursesUpdatedAfter(minRevision)
        logging.info(
            "SendCourseToSubcriptorsUseCase: %d cursos actualizados después de %s",
            len(candidates),
            minRevision.isoformat(),
        )
        if not candidates:
            return 0

        areasByCourse = self._coursesRepository.getKnowledgeAreasByCourseIds(
            [record.id for record in candidates]
        )

        # La marca de agua sube al maximo de TODOS los candidatos, no solo de los que
        # coincidieron. Antes solo avanzaba con el curso coincidente mas nuevo, asi que
        # un chat cuyos filtros no coincidian con nada nunca avanzaba y volvia a
        # recorrer todo su historico en cada corrida.
        maxUpdatedAt = max(_asUtc(record.updatedAt) for record in candidates)

        for chat in chatConfigs:
            if chat.lastRevision is None:
                continue

            matched: List[CourseRecordDto] = [
                record
                for record in candidates
                if courseMatchesChat(record, areasByCourse.get(record.id, []), chat)
            ]

            try:
                for record in matched:
                    self._notifier.sendCourseToChat(chat.id, self._toShowCourse(record, areasByCourse))

                watermark = nextWatermark(_asUtc(chat.lastRevision), maxUpdatedAt)
                if watermark != _asUtc(chat.lastRevision):
                    chat.lastRevision = watermark
                    self._databaseRepository.updateChatConfig(chat)
                    logging.info(
                        "SendCourseToSubcriptorsUseCase: lastrevision del chat %s avanzada a %s",
                        chat.id,
                        watermark.isoformat(),
                    )

                totalSent += len(matched)
                logging.info(
                    "SendCourseToSubcriptorsUseCase: el chat %s recibió %d curso(s)",
                    chat.id,
                    len(matched),
                )
            except InvalidTelegramChatError as error:
                logging.warning(
                    "SendCourseToSubcriptorsUseCase: chat inválido %s; se omitirá en futuros envíos",
                    error.chat_id,
                )
                if self._onInvalidChat is not None:
                    try:
                        self._onInvalidChat(error)
                    except Exception:
                        logging.exception(
                            "SendCourseToSubcriptorsUseCase: error desuscribiendo el chat %s",
                            error.chat_id,
                        )
            except Exception:
                logging.exception("SendCourseToSubcriptorsUseCase: error procesando el chat %s", chat.id)

        logging.info("SendCourseToSubcriptorsUseCase: total de cursos enviados %d", totalSent)
        return totalSent

    def _toShowCourse(
        self, record: CourseRecordDto, areasByCourse: dict
    ) -> ShowCourseModel:
        return courseRecordToShowCourseModel(record, areasByCourse.get(record.id, []))