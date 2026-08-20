import logging
from typing import Dict, List, Optional

from psycopg import sql

from src.domain.model.chatConfigModel import ChatConfig
from src.domain.repository.databaseRepository import (
    ChatNewCourses,
    DatabaseCourseFilters,
    DatabaseRepository,
)
from src.infraestructure.dto.database.courseDto import CoursesDto
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
    ("courses_sources", "source", "source_name", "c.source_id"),
]

COURSES_SELECT_COLUMNS_CO = [
    "co.id",
    "co.source_id",
    "co.title",
    "co.url",
    "co.uni_countries",
    "co.course_university",
    "co.uni_languages",
    "co.course_levels",
    "co.start_class_date",
    "co.end_class_date",
    "co.start_inscription_date",
    "co.end_inscription_date",
    "co.description",
    "co.study_hours",
    "co.slots",
    "co.modified_date",
]

CATALOG_JOINS_CO = [
    ("countries", "country", "country_name", "co.uni_countries"),
    ("universities", "university", "university_name", "co.course_university"),
    ("languages", "language", "language_name", "co.uni_languages"),
    ("course_levels", "course_level", "course_level_name", "co.course_levels"),
    ("courses_sources", "source", "source_name", "co.source_id"),
]

COURSES_COLUMNS = [
    "source_id",
    "title",
    "url",
    "uni_countries",
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
    def deleteCoursesBySource(self, sourceId: int) -> None:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("DELETE FROM courses WHERE source_id = %s"), (sourceId,))
        logging.info("PostgresDatabaseRepositoryImp: se eliminaron los cursos de la tabla courses con source_id=%s", sourceId)

    def saveCourses(self, courseModels: List[CourseModel]) -> int:
        totalCourses = len(courseModels)
        logging.info("PostgresDatabaseRepositoryImp: convirtiendo dto a model para guardar %d cursos en la tabla courses", totalCourses)
        courses = [courseModelToCoursesDto(course) for course in courseModels]
        if not courses:
            logging.info("PostgresDatabaseRepositoryImp: se insertaron 0 cursos en la tabla courses")
            return 0

        connection = get_db_connection()

        insertDisciplinaryQuery = sql.SQL(
            "INSERT INTO course_disciplinary_fields (course_id, disciplinary_field_id) VALUES (%s, %s)"
        )

        # Lotes de 1000 cursos: el protocolo de PostgreSQL limita a 65535 parámetros por sentencia
        # (1000 cursos x 15 columnas = 15000 parámetros por lote, muy por debajo del límite).
        BATCH_SIZE = 1000
        disciplinaryPairs = []
        with connection.cursor() as cursor:
            courseIds = []
            for start in range(0, len(courses), BATCH_SIZE):
                batch = courses[start : start + BATCH_SIZE]
                rowPlaceholders = (
                    sql.SQL("(")
                    + sql.SQL(", ").join(sql.Placeholder() for _ in COURSES_COLUMNS)
                    + sql.SQL(")")
                )
                insertQuery = sql.SQL(
                    "INSERT INTO courses ({columns}) VALUES {rows} RETURNING id"
                ).format(
                    columns=sql.SQL(", ").join(sql.Identifier(column) for column in COURSES_COLUMNS),
                    rows=sql.SQL(", ").join(rowPlaceholders for _ in batch),
                )
                batchParams = [value for course in batch for value in self._courseToRow(course)]
                cursor.execute(insertQuery, batchParams)
                batchIds = [row["id"] for row in cursor.fetchall()]
                if len(batchIds) != len(batch):
                    raise RuntimeError(
                        f"El número de ids devueltos ({len(batchIds)}) no coincide con el número de cursos insertados en el lote ({len(batch)})"
                    )
                courseIds.extend(batchIds)

            for courseId, course in zip(courseIds, courses):
                for disciplinaryFieldId in course.disciplinary_fields or []:
                    disciplinaryPairs.append((courseId, disciplinaryFieldId))
            if disciplinaryPairs:
                cursor.executemany(insertDisciplinaryQuery, disciplinaryPairs)

        logging.info("PostgresDatabaseRepositoryImp: se insertaron %d cursos en la tabla courses", len(courses))
        return len(courses)

    def getCourses(self, filters: DatabaseCourseFilters) -> List[ShowCourseModel]:
        conditions: List[sql.Composable] = []
        params: list = []

        catalogFilters = [
            ("uni_countries", filters.countryId),
            ("course_university", filters.universityId),
            ("uni_languages", filters.languageId),
            ("course_levels", filters.courseLevelId),
        ]
        for column, filterId in catalogFilters:
            if filterId is None:
                continue
            conditions.append(sql.SQL("c.{col} = %s").format(col=sql.Identifier(column)))
            params.append(filterId)

        if filters.disciplinaryFieldId is not None:
            conditions.append(
                sql.SQL(
                    "EXISTS (SELECT 1 FROM course_disciplinary_fields cdf "
                    "WHERE cdf.course_id = c.id AND cdf.disciplinary_field_id = %s)"
                )
            )
            params.append(filters.disciplinaryFieldId)

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
        selectColumns.append(
            sql.SQL(
                "COALESCE((SELECT string_agg(BTRIM(df.disciplinary_field), ', ' "
                "ORDER BY BTRIM(df.disciplinary_field)) "
                "FROM course_disciplinary_fields cdf "
                "JOIN disciplinary_fields df ON df.id = cdf.disciplinary_field_id "
                "WHERE cdf.course_id = c.id), '') AS disciplinary_fields"
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

    def getNewCoursesForChats(self) -> List[ChatNewCourses]:
        selectColumns = [sql.SQL(column) for column in COURSES_SELECT_COLUMNS_CO]
        for table, valueColumn, alias, joinColumn in CATALOG_JOINS_CO:
            selectColumns.append(
                sql.SQL("BTRIM({table}.{value_col}) AS {alias}").format(
                    table=sql.Identifier(table),
                    value_col=sql.Identifier(valueColumn),
                    alias=sql.Identifier(alias),
                )
            )
        selectColumns.append(
            sql.SQL(
                "COALESCE((SELECT string_agg(BTRIM(df.disciplinary_field), ', ' "
                "ORDER BY BTRIM(df.disciplinary_field)) "
                "FROM course_disciplinary_fields cdf "
                "JOIN disciplinary_fields df ON df.id = cdf.disciplinary_field_id "
                "WHERE cdf.course_id = co.id), '') AS disciplinary_fields"
            )
        )
        selectColumns.append(sql.SQL("cfg.id AS chat_id"))

        conditions = [
            sql.SQL("(cfg.uni_countries IS NULL OR cfg.uni_countries = co.uni_countries)"),
            sql.SQL("(cfg.course_university IS NULL OR cfg.course_university = co.course_university)"),
            sql.SQL("(cfg.uni_languages IS NULL OR cfg.uni_languages = co.uni_languages)"),
            sql.SQL("(cfg.course_levels IS NULL OR cfg.course_levels = co.course_levels)"),
            sql.SQL(
                "(cfg.disciplinary_field IS NULL OR EXISTS (SELECT 1 FROM course_disciplinary_fields cdf "
                "WHERE cdf.course_id = co.id AND cdf.disciplinary_field_id = cfg.disciplinary_field))"
            ),
            sql.SQL(
                "(cfg.key_word IS NULL OR co.title ILIKE '%' || TRIM(cfg.key_word) || '%' "
                "OR co.description ILIKE '%' || TRIM(cfg.key_word) || '%')"
            ),
            sql.SQL("(cfg.lastrevision IS NULL OR co.modified_date > cfg.lastrevision)"),
        ]

        query = sql.SQL(
            "SELECT {columns} FROM chatconfigs AS cfg CROSS JOIN courses AS co"
        ).format(columns=sql.SQL(", ").join(selectColumns))
        for table, valueColumn, alias, joinColumn in CATALOG_JOINS_CO:
            query = query + sql.SQL(" LEFT JOIN {table} ON {table}.id = {join}").format(
                table=sql.Identifier(table),
                join=sql.SQL(joinColumn),
            )
        query = query + sql.SQL(" WHERE cfg.is_subscribed = TRUE")
        query = query + sql.SQL(" AND ") + sql.SQL(" AND ").join(conditions)
        query = query + sql.SQL(" ORDER BY cfg.id, co.modified_date DESC NULLS LAST")

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        coursesByChat: Dict[int, List[ShowCourseModel]] = {}
        for row in rows:
            chatId = row["chat_id"]
            coursesByChat.setdefault(chatId, []).append(self._rowToShowCourseModel(row))

        matches = [
            ChatNewCourses(chatId=chatId, courses=courses)
            for chatId, courses in coursesByChat.items()
        ]
        logging.info(
            "PostgresDatabaseRepositoryImp: getNewCoursesForChats devolvió %d filas para %d chats",
            len(rows),
            len(matches),
        )
        return matches

    def _rowToShowCourseModel(self, row: dict) -> ShowCourseModel:
        return ShowCourseModel(
            source=row.get("source_name"),
            title=row.get("title"),
            university=row.get("university_name"),
            url=row.get("url"),
            country=row.get("country_name"),
            language=row.get("language_name"),
            disciplinaryFields=self._rowDisciplinaryFields(row.get("disciplinary_fields")),
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

    def _rowDisciplinaryFields(self, value: Optional[str]) -> Optional[List[str]]:
        if not value:
            return None
        names = [part.strip() for part in value.split(",") if part.strip()]
        return names or None

    def _courseToRow(self, dto: CoursesDto) -> tuple:
        return (
            dto.source_id,
            dto.title,
            dto.url,
            dto.uni_countries,
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