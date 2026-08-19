import logging
import os
import pathlib
import sys

import psycopg
from dotenv import load_dotenv

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.config.defaultValuesCatalog import APP_COURSE_SOURCES, catalogValues

load_dotenv()

if not os.getenv("DB_URL"):
    raise RuntimeError("Falta variable de entorno DB_URL")

CATALOG_TABLES = {
    "universities": "university",
    "disciplinary_fields": "disciplinary_field",
    "countries": "country",
    "languages": "language",
    "course_levels": "course_level",
}

CREATE_CATALOG_TABLE = """
CREATE TABLE IF NOT EXISTS {table} (
    id INT PRIMARY KEY,
    {value_column} VARCHAR(100) NOT NULL UNIQUE
)
"""

CREATE_CHAT_CONFIGS_TABLE = """
CREATE TABLE IF NOT EXISTS chatconfigs (
    id BIGINT PRIMARY KEY,
    lastrevision DATE DEFAULT CURRENT_DATE,
    is_subscribed BOOLEAN NOT NULL DEFAULT TRUE,
    uni_countries INT REFERENCES countries(id),
    disciplinary_field INT REFERENCES disciplinary_fields(id),
    course_university INT REFERENCES universities(id),
    uni_languages INT REFERENCES languages(id),
    course_levels INT REFERENCES course_levels(id),
    key_word VARCHAR(50)
)
"""

CREATE_COURSES_SOURCES_TABLE = """
CREATE TABLE IF NOT EXISTS courses_sources (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL UNIQUE
)
"""

CREATE_COURSES_TABLE = """
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES courses_sources(id),
    title VARCHAR(255),
    url TEXT,
    uni_countries INT REFERENCES countries(id),
    course_university INT REFERENCES universities(id),
    uni_languages INT REFERENCES languages(id),
    course_levels INT REFERENCES course_levels(id),
    start_class_date DATE,
    end_class_date DATE,
    start_inscription_date DATE,
    end_inscription_date DATE,
    description TEXT,
    study_hours INT,
    slots INT,
    modified_date DATE
)
"""

CREATE_COURSE_DISCIPLINARY_FIELDS_TABLE = """
CREATE TABLE IF NOT EXISTS course_disciplinary_fields (
    course_id INT REFERENCES courses(id) ON DELETE CASCADE,
    disciplinary_field_id INT REFERENCES disciplinary_fields(id),
    PRIMARY KEY (course_id, disciplinary_field_id)
)
"""

INSERT_CATALOG_VALUE = """
INSERT INTO {table} (id, {value_column}) VALUES (%s, %s)
ON CONFLICT (id) DO NOTHING
"""

INSERT_COURSE_SOURCE = """
INSERT INTO courses_sources (source) VALUES (%s)
ON CONFLICT (source) DO NOTHING
"""


def create_tables():
    with psycopg.connect(os.getenv("DB_URL"), autocommit=True) as connection:
        with connection.cursor() as cursor:
            for table, value_column in CATALOG_TABLES.items():
                cursor.execute(CREATE_CATALOG_TABLE.format(table=table, value_column=value_column))
            cursor.execute(CREATE_CHAT_CONFIGS_TABLE)
            cursor.execute(CREATE_COURSES_SOURCES_TABLE)
            cursor.execute(CREATE_COURSES_TABLE)
            cursor.execute(CREATE_COURSE_DISCIPLINARY_FIELDS_TABLE)

            # La extensión pg_trgm puede requerir privilegios de superusuario en PostgreSQL
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_courses_filters ON courses (uni_countries, uni_languages, course_levels, course_university)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_course_disc_fields_disc ON course_disciplinary_fields (disciplinary_field_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_courses_title_trgm ON courses USING gin (title gin_trgm_ops)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_courses_description_trgm ON courses USING gin (description gin_trgm_ops)")

            for sourceName in APP_COURSE_SOURCES.values():
                cursor.execute(INSERT_COURSE_SOURCE, (sourceName,))

            for table, value_column in CATALOG_TABLES.items():
                values = catalogValues(table)
                for catalog_id, value in values:
                    cursor.execute(
                        INSERT_CATALOG_VALUE.format(table=table, value_column=value_column),
                        (catalog_id, value),
                    )
                logging.info("Seed: %d valores insertados en catálogo '%s'", len(values), table)


if __name__ == "__main__":
    create_tables()
    print("Tablas creadas correctamente.")