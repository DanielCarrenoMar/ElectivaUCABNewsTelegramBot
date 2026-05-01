import asyncio
from datetime import date, datetime
import os
import time
from typing import Optional, TypedDict

import psycopg
import psycopg.errors
from psycopg import sql
from psycopg.rows import dict_row
from dotenv import load_dotenv

from data.types import ChatConfig

load_dotenv()

if not os.getenv("DB_URL"):
    raise RuntimeError("Falta variable de entorno DB_URL")

_databaseConnection = None
DB_CONNECTION_RETRY_DELAY_SECONDS = float(os.getenv("DB_CONNECTION_RETRY_DELAY_SECONDS", "2"))
DB_CONNECTION_MAX_RETRIES = int(os.getenv("DB_CONNECTION_MAX_RETRIES", "3"))

def get_db_connection():
    return _get_db_connection_sync()

async def get_db_connection_async():
    return await _get_db_connection_async()

def _get_db_connection_sync():
    global _databaseConnection

    last_error = None
    for attempt in range(DB_CONNECTION_MAX_RETRIES + 1):
        try:
            if _databaseConnection is None or _databaseConnection.closed:
                _databaseConnection = psycopg.connect(os.getenv("DB_URL"), autocommit=True)
            else:
                _databaseConnection.execute("SELECT 1")
            return _databaseConnection
        except (psycopg.OperationalError, psycopg.errors.OperationalError) as error:
            last_error = error
            _databaseConnection = None
            if attempt < DB_CONNECTION_MAX_RETRIES:
                time.sleep(DB_CONNECTION_RETRY_DELAY_SECONDS)

    if last_error is not None:
        raise last_error

    raise RuntimeError("No se pudo conectar a la base de datos")

async def _get_db_connection_async():
    global _databaseConnection

    last_error = None
    for attempt in range(DB_CONNECTION_MAX_RETRIES + 1):
        try:
            if _databaseConnection is None or _databaseConnection.closed:
                _databaseConnection = await asyncio.to_thread(
                    psycopg.connect,
                    os.getenv("DB_URL"),
                    autocommit=True,
                )
            else:
                await asyncio.to_thread(_databaseConnection.execute, "SELECT 1")
            return _databaseConnection
        except (psycopg.OperationalError, psycopg.errors.OperationalError) as error:
            last_error = error
            _databaseConnection = None
            if attempt < DB_CONNECTION_MAX_RETRIES:
                await asyncio.sleep(DB_CONNECTION_RETRY_DELAY_SECONDS)

    if last_error is not None:
        raise last_error

    raise RuntimeError("No se pudo conectar a la base de datos")

class ChatConfigRow(TypedDict, total=False):
    id: int
    issubscribed: bool
    lastrevision: date
    uni_countries: Optional[str]
    disciplinary_field: Optional[str]
    course_university: Optional[str]
    uni_languages: Optional[str]
    course_levels: Optional[str]
    uni_search: Optional[str]
    

def _rowToChatConfig(row: ChatConfigRow) -> ChatConfig:

    return {
        "filters": {
            "uni_countries": row.get("uni_countries"),
            "disciplinary_field": row.get("disciplinary_field"),
            "course_university": row.get("course_university"),
            "uni_languages": row.get("uni_languages"),
            "course_levels": row.get("course_levels"),
            "uni_search": row.get("uni_search"),
        },
        "lastRevision": row.get("lastrevision").isoformat(),
        "isSubcribed": row.get("issubscribed"),
    }

def chatConfigToRow(chatId: int, config: ChatConfig) -> ChatConfigRow:
    filters = config["filters"]

    return {
        "id": chatId,
        "issubscribed": config["isSubcribed"],
        "lastrevision": datetime.fromisoformat(config["lastRevision"]),
        "uni_countries": filters.get("uni_countries"),
        "disciplinary_field": filters.get("disciplinary_field"),
        "course_university": filters.get("course_university"),
        "uni_languages": filters.get("uni_languages"),
        "course_levels": filters.get("course_levels"),
        "uni_search": filters.get("uni_search"),
    }


def _fecthChatConfig(chatId: int, cursor: psycopg.cursor) -> Optional[ChatConfigRow]:
    cursor.execute(
    sql.SQL(
        """
        SELECT id, issubscribed, lastrevision,
                    uni_countries, disciplinary_field, course_university,
                    uni_languages, course_levels, uni_search
            FROM chatconfig
            WHERE id = %s
            """
        ),
        (chatId,),
    )
    row = cursor.fetchone()

    if row is None:
        return None

    return row

def getOrCreateChatConfig(chatId: int) -> ChatConfig:
    with get_db_connection().cursor(row_factory=dict_row) as cursor:
        row = _fecthChatConfig(chatId, cursor)

        if row is None:
            cursor.execute(
                sql.SQL(
                    """
                    INSERT INTO chatconfig
                        (id, issubscribed,
                         uni_countries, disciplinary_field, course_university,
                         uni_languages, course_levels, uni_search)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """
                ),
                (
                    chatId,
                    False,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            )
            get_db_connection().commit()
            row = _fecthChatConfig(chatId, cursor)

            if row is None:
                raise RuntimeError("Error al crear la configuración del chat.")

        return _rowToChatConfig(row)


def updateChatConfig(chatId: int, config: ChatConfig) -> ChatConfig:
    row = chatConfigToRow(chatId, config)

    with get_db_connection().cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            sql.SQL(
                """
                INSERT INTO chatconfig
                    (id, issubscribed, lastrevision,
                     uni_countries, disciplinary_field, course_university,
                     uni_languages, course_levels, uni_search)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    issubscribed = EXCLUDED.issubscribed,
                    lastrevision = EXCLUDED.lastrevision,
                    uni_countries = EXCLUDED.uni_countries,
                    disciplinary_field = EXCLUDED.disciplinary_field,
                    course_university = EXCLUDED.course_university,
                    uni_languages = EXCLUDED.uni_languages,
                    course_levels = EXCLUDED.course_levels,
                    uni_search = EXCLUDED.uni_search
                """
            ),
            (
                chatId,
                row["issubscribed"],
                row["lastrevision"],
                row["uni_countries"],
                row["disciplinary_field"],
                row["course_university"],
                row["uni_languages"],
                row["course_levels"],
                row["uni_search"],
            ),
        )
        get_db_connection().commit()

        return _fecthChatConfig(chatId, cursor)


def getAllChatConfigs() -> dict[int, ChatConfig]:
    chatConfigs: dict[int, ChatConfig] = {}

    with get_db_connection().cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            sql.SQL(
                """
                SELECT id, issubscribed, lastrevision,
                       uni_countries, disciplinary_field, course_university,
                       uni_languages, course_levels, uni_search
                FROM chatconfig
                """
            )
        )

        for row in cursor.fetchall():
            chatConfigs[int(row["id"])] = _rowToChatConfig(row)

    return chatConfigs

