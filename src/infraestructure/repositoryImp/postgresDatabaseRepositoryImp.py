import logging
from typing import List, Optional

from psycopg import sql

from src.domain.model.chatConfigModel import ChatConfig
from src.domain.repository.databaseRepository import DatabaseCourseFilters, DatabaseRepository
from src.domain.model.courseModel import ShowCourseModel
from src.infraestructure.dbConnection import get_db_connection
from src.domain.model.courseModel import CourseModel
from src.infraestructure.mapper.chatConfigMapper import chatConfigToChatConfigsDto
from src.infraestructure.mapper.courseDtoMapper import courseModelToCoursesDto

COURSES_SELECT_COLUMNS = [
    "c.id",
    "c.source_id",
    "c.title",
    "c.url",
    "c.uni_countries",
    "c.disciplinary_field",
    "c.course_university",
    "c.uni_languages",
    "c.course_levels",
    "c.start_class_date",
    "c.end_class_date",
    "c.start_inscription_date",
    "c.end_inscription_date",
    "c.description",
    "c.study_hours",
    "c.slots",
    "c.modified_date",
]

CATALOG_JOINS = [
    ("countries", "country", "country_name", "c.uni_countries"),
    ("universities", "university", "university_name", "c.course_university"),
    ("languages", "language", "language_name", "c.uni_languages"),
    ("course_levels", "course_level", "course_level_name", "c.course_levels"),
    ("disciplinary_fields", "disciplinary_field", "disciplinary_field_name", "c.disciplinary_field"),
    ("courses_sources", "source", "source_name", "c.source_id"),
]

COURSES_COLUMNS = [
    "source_id",
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
    def deleteAllCourses(self) -> None:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("DELETE FROM courses"))
        logging.info("PostgresDatabaseRepositoryImp: se eliminaron todos los cursos de la tabla courses")

    def saveCourses(self, courseModels: List[CourseModel]) -> int:
        courses = [courseModelToCoursesDto(course) for course in courseModels]
        connection = get_db_connection()

        insertQuery = sql.SQL(
            "INSERT INTO courses ({columns}) VALUES ({placeholders})"
        ).format(
            columns=sql.SQL(", ").join(sql.Identifier(column) for column in COURSES_COLUMNS),
            placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in COURSES_COLUMNS),
        )

        with connection.cursor() as cursor:
            for course in courses:
                cursor.execute(insertQuery, self._courseToRow(course))

        logging.info("PostgresDatabaseRepositoryImp: se insertaron %d cursos en la tabla courses", len(courses))
        return len(courses)

    def getCourses(self, filters: DatabaseCourseFilters) -> List[ShowCourseModel]:
        conditions: List[sql.Composable] = []
        params: list = []

        catalogFilters = [
            ("uni_countries", filters.countryId),
            ("disciplinary_field", filters.disciplinaryFieldId),
            ("course_university", filters.universityId),
            ("uni_languages", filters.languageId),
            ("course_levels", filters.courseLevelId),
        ]
        for column, filterId in catalogFilters:
            if filterId is None:
                continue
            conditions.append(sql.SQL("(c.{col} = %s OR %s IS NULL)").format(col=sql.Identifier(column)))
            params.extend([filterId, filterId])

        if filters.keyword:
            conditions.append(sql.SQL("(c.title ILIKE %s OR c.description ILIKE %s)"))
            params.extend([f"%{filters.keyword}%", f"%{filters.keyword}%"])

        if filters.minModifiedDate is not None:
            conditions.append(sql.SQL("c.modified_date > %s"))
            params.append(filters.minModifiedDate)

        selectColumns = [sql.SQL(column) for column in COURSES_SELECT_COLUMNS]
        for table, valueColumn, alias, joinColumn in CATALOG_JOINS:
            selectColumns.append(
                sql.SQL("BTRIM({table}.{value_col}) AS {alias}").format(
                    table=sql.Identifier(table),
                    value_col=sql.Identifier(valueColumn),
                    alias=sql.Identifier(alias),
                )
            )

        query = sql.SQL("SELECT {columns} FROM courses AS c").format(
            columns=sql.SQL(", ").join(selectColumns)
        )
        for table, valueColumn, alias, joinColumn in CATALOG_JOINS:
            query = query + sql.SQL(" LEFT JOIN {table} ON {table}.id = {join}").format(
                table=sql.Identifier(table),
                join=sql.SQL(joinColumn),
            )
        if conditions:
            query = query + sql.SQL(" WHERE ") + sql.SQL(" AND ").join(conditions)
        query = query + sql.SQL(" ORDER BY c.modified_date DESC NULLS LAST")

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        courses = [self._rowToShowCourseModel(row) for row in rows]
        logging.info("PostgresDatabaseRepositoryImp: getCourses devolvió %d cursos", len(courses))
        return courses

    def _rowToShowCourseModel(self, row: dict) -> ShowCourseModel:
        return ShowCourseModel(
            source=row.get("source_name"),
            title=row.get("title"),
            university=row.get("university_name"),
            url=row.get("url"),
            country=row.get("country_name"),
            language=row.get("language_name"),
            disciplinaryField=row.get("disciplinary_field_name"),
            courseLevel=row.get("course_level_name"),
            startClassDate=row.get("start_class_date"),
            endClassDate=row.get("end_class_date"),
            startInscriptionDate=row.get("start_inscription_date"),
            endInscriptionDate=row.get("end_inscription_date"),
            description=row.get("description"),
            studyHours=row.get("study_hours"),
            slots=row.get("slots"),
            modifiedDate=row.get("modified_date"),
        )

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

    def updateChatConfig(self, chatConfig: ChatConfig) -> None:
        dto = chatConfigToChatConfigsDto(chatConfig)
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "UPDATE chatconfigs SET is_subscribed = %s, lastrevision = %s, "
                    "uni_countries = %s, disciplinary_field = %s, course_university = %s, "
                    "uni_languages = %s, course_levels = %s, key_word = %s WHERE id = %s"
                ),
                (
                    dto.is_subscribed,
                    dto.last_revision,
                    dto.uni_countries,
                    dto.disciplinary_field,
                    dto.course_university,
                    dto.uni_languages,
                    dto.course_levels,
                    dto.key_word,
                    dto.id,
                ),
            )
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

    def _courseToRow(self, dto: CoursesDto) -> tuple:
        return (
            dto.source_id,
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