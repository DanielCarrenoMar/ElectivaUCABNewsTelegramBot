import logging
from typing import List, Optional

from psycopg import sql

from src.domain.model.chatConfigModel import ChatConfig
from src.domain.repository.databaseRepository import DatabaseRepository
from src.infraestructure.dbConnection import get_db_connection
from src.infraestructure.mapper.chatConfigMapper import (
    chatConfigToChatConfigsDto,
    chatConfigsDtoToChatConfig,
)

# chatconfigs es la unica tabla que queda en la base propia: guarda la suscripcion
# de cada chat y sus filtros. Los filtros guardan la clave natural del catalogo de
# cursos (iso_code, name, code, academic_levels.id), no un id propio, porque no hay
# llave foranea entre las dos bases de datos.
CHAT_CONFIG_COLUMNS = [
    "id",
    "lastrevision",
    "is_subscribed",
    "country_iso_code",
    "course_university",
    "course_language_code",
    "course_level_id",
    "disciplinary_field",
    "key_word",
]

# El id es la llave primaria: en el UPDATE va al final, como criterio del WHERE.
CHAT_CONFIG_UPDATABLE_COLUMNS = [column for column in CHAT_CONFIG_COLUMNS if column != "id"]


class PostgresDatabaseRepositoryImp(DatabaseRepository):
    """Acceso a la base propia (DB_URL): suscripciones y filtros de los chats."""

    def getOrCreateChatConfig(self, chatId: int) -> ChatConfig:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            row = self._fetchChatConfig(cursor, chatId)
            if row is None:
                cursor.execute(
                    sql.SQL("INSERT INTO chatconfigs (id) VALUES (%s) ON CONFLICT (id) DO NOTHING"),
                    (chatId,),
                )
                row = self._fetchChatConfig(cursor, chatId)
                if row is None:
                    raise RuntimeError(f"Error al crear la configuración del chat {chatId}")

        logging.info("PostgresDatabaseRepositoryImp: configuración del chat %s obtenida o creada", chatId)
        return self._rowToChatConfig(row)

    def getSubcriptorsChatConfig(self) -> List[ChatConfig]:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT {columns} FROM chatconfigs WHERE is_subscribed = TRUE ORDER BY id").format(
                    columns=sql.SQL(", ").join(sql.Identifier(column) for column in CHAT_CONFIG_COLUMNS)
                )
            )
            rows = cursor.fetchall()

        chatConfigs = [self._rowToChatConfig(row) for row in rows]
        logging.info(
            "PostgresDatabaseRepositoryImp: se obtuvieron %d configuraciones de chat suscritas",
            len(chatConfigs),
        )
        return chatConfigs

    def updateChatConfig(self, chatConfig: ChatConfig) -> None:
        dto = chatConfigToChatConfigsDto(chatConfig)
        # La columna se llama lastrevision y el campo del DTO last_revision, asi que
        # el orden de los valores se fija aqui y no con model_dump: ese devolveria
        # las claves del DTO, no los nombres de columna.
        columnValues = {
            "lastrevision": dto.last_revision,
            "is_subscribed": dto.is_subscribed,
            "country_iso_code": dto.country_iso_code,
            "course_university": dto.course_university,
            "course_language_code": dto.course_language_code,
            "course_level_id": dto.course_level_id,
            "disciplinary_field": dto.disciplinary_field,
            "key_word": dto.key_word,
        }

        assignments = sql.SQL(", ").join(
            sql.SQL("{column} = %s").format(column=sql.Identifier(column))
            for column in CHAT_CONFIG_UPDATABLE_COLUMNS
        )
        query = sql.SQL("UPDATE chatconfigs SET {assignments} WHERE id = %s").format(assignments=assignments)

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(query, [columnValues[column] for column in CHAT_CONFIG_UPDATABLE_COLUMNS] + [dto.id])
        logging.info("PostgresDatabaseRepositoryImp: configuración del chat %s actualizada", chatConfig.id)

    def _fetchChatConfig(self, cursor, chatId: int) -> Optional[dict]:
        cursor.execute(
            sql.SQL("SELECT {columns} FROM chatconfigs WHERE id = %s").format(
                columns=sql.SQL(", ").join(sql.Identifier(column) for column in CHAT_CONFIG_COLUMNS)
            ),
            (chatId,),
        )
        return cursor.fetchone()

    def _rowToChatConfig(self, row: dict) -> ChatConfig:
        keyWord = (row.get("key_word") or "").strip() or None

        return chatConfigsDtoToChatConfig(
            {
                "id": row.get("id"),
                "last_revision": row.get("lastrevision"),
                "is_subscribed": row.get("is_subscribed", True),
                "country_iso_code": row.get("country_iso_code"),
                "course_university": row.get("course_university"),
                "course_language_code": row.get("course_language_code"),
                "course_level_id": row.get("course_level_id"),
                "disciplinary_field": row.get("disciplinary_field"),
                "key_word": keyWord,
            }
        )