import logging
from datetime import datetime
from typing import Dict, List

from psycopg import sql

from src.domain.model.courseModel import CatalogEntry, CourseRecordDto
from src.domain.repository.coursesRepository import CoursesRepository
from src.infraestructure.dbConnection import get_courses_db_connection
from src.infraestructure.mapper.courseRecordMapper import rowToCourseRecordDto

# Columnas de la consulta de cursos con su alias explicito. El alias es lo que
# lee rowToCourseRecordDto, asi que cada columna queda inequivoca aunque dos
# tablas tengan un nombre igual (courses.title vs knowledge_areas.title).
COURSES_COLUMNS = [
    ("c", "id", "id"),
    ("c", "title", "title"),
    ("c", "description", "description"),
    ("c", "site_url", "site_url"),
    ("c", "modality", "modality"),
    ("c", "credits", "credits"),
    ("c", "enrollment_start", "enrollment_start"),
    ("c", "enrollment_end", "enrollment_end"),
    ("c", "course_start", "course_start"),
    ("c", "course_end", "course_end"),
    ("c", "total_seats", "total_seats"),
    ("c", "available_seats", "available_seats"),
    ("c", "updated_at", "updated_at"),
    ("ca", "name", "campus_name"),
    ("un", "name", "university_name"),
    ("ci", "name", "city_name"),
    ("ct", "iso_code", "country_iso_code"),
    ("ct", "name", "country_name"),
    ("lg", "code", "language_code"),
    ("lg", "name", "language_name"),
    ("al", "id", "academic_level_id"),
    ("al", "name", "academic_level_name"),
    ("s", "name", "source_name"),
]

# campuses, universities, languages y academic_levels son llaves foraneas NOT NULL
# de courses, asi que un INNER JOIN no descarta ningun curso. En cambio
# campus.city_id y courses.source_id son nulables: 2117 de 4167 cursos no tienen
# ciudad y por lo tanto no llegan a ningun pais. Por eso ciudad y pais van con
# LEFT JOIN para que esos cursos salgan igual, con el pais en None.
INNER_JOINS = [
    ("campuses", "ca", sql.SQL("ca.id = c.campus_id")),
    ("universities", "un", sql.SQL("un.id = ca.university_id")),
    ("languages", "lg", sql.SQL("lg.code = c.language_code")),
    ("academic_levels", "al", sql.SQL("al.id = c.academic_level_id")),
]

LEFT_JOINS = [
    ("cities", "ci", sql.SQL("ci.id = ca.city_id")),
    ("countries", "ct", sql.SQL("ct.id = ci.country_id")),
    ("sources", "s", sql.SQL("s.id = c.source_id")),
]

# El filtro por fecha va abajo en SQL en vez de paginar en Python. No se pone un
# LIMIT fijo: truncar en silencio dejaria cursos sin notificar.
COURSES_QUERY = sql.SQL(
    "SELECT {columns} FROM courses AS c "
    "{innerJoins} {leftJoins} "
    "WHERE c.is_active = TRUE AND c.updated_at > %s "
    "ORDER BY c.updated_at DESC"
).format(
    columns=sql.SQL(", ").join(
        sql.SQL("{table}.{column} AS {alias}").format(
            table=sql.Identifier(table),
            column=sql.Identifier(column),
            alias=sql.Identifier(alias),
        )
        for table, column, alias in COURSES_COLUMNS
    ),
    innerJoins=sql.SQL(" ").join(
        sql.SQL("INNER JOIN {table} AS {alias} ON {condition}").format(
            table=sql.Identifier(table),
            alias=sql.Identifier(alias),
            condition=condition,
        )
        for table, alias, condition in INNER_JOINS
    ),
    leftJoins=sql.SQL(" ").join(
        sql.SQL("LEFT JOIN {table} AS {alias} ON {condition}").format(
            table=sql.Identifier(table),
            alias=sql.Identifier(alias),
            condition=condition,
        )
        for table, alias, condition in LEFT_JOINS
    ),
)

# Una sola consulta para todos los ids, no una por curso: la version anterior
# usaba un string_agg correlacionado por fila y eso es un N+1 disfrazado. El
# orden por nombre hace estable el texto del mensaje.
KNOWLEDGE_AREAS_QUERY = sql.SQL(
    "SELECT cka.course_id AS course_id, ka.name AS knowledge_area_name "
    "FROM course_knowledge_areas AS cka "
    "INNER JOIN knowledge_areas AS ka ON ka.id = cka.knowledge_area_id "
    "WHERE cka.course_id = ANY(%s) "
    "ORDER BY cka.course_id, ka.name"
)


class CoursesRepositoryImp(CoursesRepository):
    """Lectura del catalogo de cursos. Esta base es de otro sistema: aqui nunca se escribe."""

    def getCoursesUpdatedAfter(self, moment: datetime) -> List[CourseRecordDto]:
        connection = get_courses_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(COURSES_QUERY, (moment,))
            rows = cursor.fetchall()

        logging.info(
            "CoursesRepositoryImp: getCoursesUpdatedAfter devolvió %d cursos actualizados después de %s",
            len(rows),
            moment,
        )
        if not rows:
            return []

        records = [rowToCourseRecordDto(row) for row in rows]
        knowledgeAreas = self.getKnowledgeAreasByCourseIds([record.id for record in records])
        return records

    def getKnowledgeAreasByCourseIds(self, courseIds: List[str]) -> Dict[str, List[str]]:
        if not courseIds:
            logging.info("CoursesRepositoryImp: getKnowledgeAreasByCourseIds sin ids, devuelve vacío")
            return {}

        connection = get_courses_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(KNOWLEDGE_AREAS_QUERY, (list(courseIds),))
            rows = cursor.fetchall()

        areasByCourse: Dict[str, List[str]] = {}
        for row in rows:
            areasByCourse.setdefault(row["course_id"], []).append(row["knowledge_area_name"])

        logging.info(
            "CoursesRepositoryImp: getKnowledgeAreasByCourseIds devolvió áreas para %d de %d cursos",
            len(areasByCourse),
            len(courseIds),
        )
        return areasByCourse

    def getCountryCatalog(self) -> List[CatalogEntry]:
        # Se devuelven los 249 paises, no solo los que usa algun curso: el teclado
        # de filtros muestra lo que ofrece el catalogo. El iso_code es unico, asi
        # que el valor del filtro no se repite.
        return self._catalogEntries("SELECT iso_code AS value, name AS label FROM countries ORDER BY name")

    def getUniversityCatalog(self) -> List[CatalogEntry]:
        return self._catalogEntries("SELECT name AS value, name AS label FROM universities ORDER BY name")

    def getLanguageCatalog(self) -> List[CatalogEntry]:
        return self._catalogEntries("SELECT code AS value, name AS label FROM languages ORDER BY name")

    def getAcademicLevelCatalog(self) -> List[CatalogEntry]:
        return self._catalogEntries("SELECT id AS value, name AS label FROM academic_levels ORDER BY name")

    def getKnowledgeAreaCatalog(self) -> List[CatalogEntry]:
        return self._catalogEntries("SELECT name AS value, name AS label FROM knowledge_areas ORDER BY name")

    def _catalogEntries(self, query: sql.Composable) -> List[CatalogEntry]:
        connection = get_courses_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        entries = [
            CatalogEntry(value=str(row["value"]), label=str(row["label"]))
            for row in rows
        ]
        logging.info("CoursesRepositoryImp: catálogo devolvió %d entradas", len(entries))
        return entries