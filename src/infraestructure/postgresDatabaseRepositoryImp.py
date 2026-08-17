import logging
from datetime import date
from typing import List, Optional

from psycopg import sql

from src.domain.chatConfigModel import ChatConfig
from src.domain.databaseRepository import DatabaseCourseFilters, DatabaseRepository
from src.domain.model.courseModel import CourseModel
from src.infraestructure.dbConnection import get_db_connection
from src.infraestructure.dto.database.courseDto import CoursesDto
from src.infraestructure.mapper.courseDtoMapper import courseDtoToCourseModel
from src.infraestructure.mapper.emoviesCatalogTranslator import EmoviesCatalogTranslator

COURSES_COLUMNS = [
    "source_id",
    "external_id",
    "title",
    "url",
    "uni_countries",
    "disciplinary_field",
    "course_university",
    "uni_languages",
    "course_levels",
    "start_class_date",
    "end_class_date",
    "start_inscription_date",
    "end_inscription_date",
    "description",
    "study_hours",
    "slots",
    "modified_date",
]

CHAT_CONFIG_COLUMNS = [
    "id",
    "is_subscribed",
    "lastrevision",
    "uni_countries",
    "disciplinary_field",
    "course_university",
    "uni_languages",
    "course_levels",
    "key_word",
]


class PostgresDatabaseRepositoryImp(DatabaseRepository):
    def __init__(self):
        self._emoviesSourceId: Optional[int] = None

    def _getSourceId(self) -> int:
        if self._emoviesSourceId is None:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SELECT id FROM courses_sources WHERE source = %s"),
                    ("emovies",),
                )
                row = cursor.fetchone()
                if row is None:
                    raise RuntimeError("No se encontró la fuente 'emovies' en courses_sources")
                self._emoviesSourceId = row["id"]
        return self._emoviesSourceId

    def deleteAllCourses(self) -> None:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("DELETE FROM courses"))
        logging.info("PostgresDatabaseRepositoryImp: se eliminaron todos los cursos de la tabla courses")

    def saveCourses(self, courses: List[CoursesDto]) -> int:
        sourceId = self._getSourceId()
        connection = get_db_connection()

        insertQuery = sql.SQL(
            "INSERT INTO courses ({columns}) VALUES ({placeholders})"
        ).format(
            columns=sql.SQL(", ").join(sql.Identifier(column) for column in COURSES_COLUMNS),
            placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in COURSES_COLUMNS),
        )

        with connection.cursor() as cursor:
            for course in courses:
                cursor.execute(insertQuery, self._courseToRow(sourceId, course))

        logging.info("PostgresDatabaseRepositoryImp: se insertaron %d cursos en la tabla courses", len(courses))
        return len(courses)

    def getCourses(self, filters: DatabaseCourseFilters) -> List[CourseModel]:
        conditions: List[sql.Composable] = []
        params: list = []

        catalogFilters = [
            ("uni_countries", filters.country_id),
            ("disciplinary_field", filters.disciplinary_field_id),
            ("course_university", filters.university_id),
            ("uni_languages", filters.language_id),
            ("course_levels", filters.course_level_id),
        ]
        for column, filterId in catalogFilters:
            if filterId is None:
                continue
            conditions.append(sql.SQL("({col} = %s OR %s IS NULL)").format(col=sql.Identifier(column)))
            params.extend([filterId, filterId])

        if filters.keyword:
            conditions.append(sql.SQL("(title ILIKE %s OR description ILIKE %s)"))
            params.extend([f"%{filters.keyword}%", f"%{filters.keyword}%"])

        if filters.min_modified_date is not None:
            conditions.append(sql.SQL("modified_date > %s"))
            params.append(filters.min_modified_date)

        query = sql.SQL("SELECT {columns} FROM courses").format(
            columns=sql.SQL(", ").join(sql.Identifier(column) for column in COURSES_COLUMNS)
        )
        if conditions:
            query = query + sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions)
        query = query + sql.SQL(" ORDER BY modified_date DESC NULLS LAST")

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        coursesDtos = [self._rowToCoursesDto(row) for row in rows]
        catalogNames = EmoviesCatalogTranslator().idToNameMaps()
        courses = [courseDtoToCourseModel(courseDto, catalogNames) for courseDto in coursesDtos]
        logging.info("PostgresDatabaseRepositoryImp: getCourses devolvió %d cursos", len(courses))
        return courses

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
                sql.SQL("SELECT {columns} FROM chatconfigs WHERE is_subscribed = TRUE").format(
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

    def updateChatLastRevision(self, chatId: int, lastRevision: date) -> None:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("UPDATE chatconfigs SET lastrevision = %s WHERE id = %s"),
                (lastRevision, chatId),
            )
        logging.info(
            "PostgresDatabaseRepositoryImp: lastrevision del chat %s actualizada a %s",
            chatId,
            lastRevision,
        )

    def updateChatSubscription(self, chatId: int, subscribed: bool) -> None:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("UPDATE chatconfigs SET is_subscribed = %s WHERE id = %s"),
                (subscribed, chatId),
            )
        logging.info(
            "PostgresDatabaseRepositoryImp: suscripción del chat %s = %s",
            chatId,
            subscribed,
        )

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

        return ChatConfig(
            id=row["id"],
            isSubscribed=row.get("is_subscribed", True),
            lastRevision=row.get("lastrevision"),
            uniCountries=row.get("uni_countries"),
            disciplinaryField=row.get("disciplinary_field"),
            courseUniversity=row.get("course_university"),
            uniLanguages=row.get("uni_languages"),
            courseLevels=row.get("course_levels"),
            keyWord=keyWord,
        )

    def _courseToRow(self, sourceId: int, dto: CoursesDto) -> tuple:
        return (
            sourceId,
            dto.external_id,
            dto.title,
            dto.url,
            dto.uni_countries,
            dto.disciplinary_field,
            dto.course_university,
            dto.uni_languages,
            dto.course_levels,
            dto.start_class_date,
            dto.end_class_date,
            dto.start_inscription_date,
            dto.end_inscription_date,
            dto.description,
            dto.study_hours,
            dto.slots,
            dto.modified_date,
        )

    def _rowToCoursesDto(self, row: dict) -> CoursesDto:
        return CoursesDto(
            id=row.get("id"),
            source_id=row.get("source_id"),
            external_id=row.get("external_id"),
            title=row.get("title") or None,
            url=row.get("url") or None,
            uni_countries=row.get("uni_countries"),
            disciplinary_field=row.get("disciplinary_field"),
            course_university=row.get("course_university"),
            uni_languages=row.get("uni_languages"),
            course_levels=row.get("course_levels"),
            start_class_date=row.get("start_class_date"),
            end_class_date=row.get("end_class_date"),
            start_inscription_date=row.get("start_inscription_date"),
            end_inscription_date=row.get("end_inscription_date"),
            description=row.get("description") or None,
            study_hours=row.get("study_hours"),
            slots=row.get("slots"),
            modified_date=row.get("modified_date"),
        )