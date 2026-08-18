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
    id SERIAL PRIMARY KEY,
    {value_column} CHAR(100) NOT NULL UNIQUE
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
    key_word CHAR(50)
)
"""

CREATE_COURSES_SOURCES_TABLE = """
CREATE TABLE IF NOT EXISTS courses_sources (
    id SERIAL PRIMARY KEY,
    source CHAR(100) NOT NULL UNIQUE
)
"""

CREATE_COURSES_TABLE = """
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES courses_sources(id),
    title VARCHAR(255),
    url TEXT,
    uni_countries INT REFERENCES countries(id),
    disciplinary_field INT REFERENCES disciplinary_fields(id),
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

INSERT_CATALOG_VALUE = """
INSERT INTO {table} ({value_column}) VALUES (%s) ON CONFLICT ({value_column}) DO NOTHING
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

            for sourceName in APP_COURSE_SOURCES.values():
                cursor.execute(INSERT_COURSE_SOURCE, (sourceName,))

            for table, value_column in CATALOG_TABLES.items():
                values = catalogValues(table)
                for value in values:
                    cursor.execute(
                        INSERT_CATALOG_VALUE.format(table=table, value_column=value_column),
                        (value,),
                    )
                logging.info("Seed: %d valores insertados en catálogo '%s'", len(values), table)


if __name__ == "__main__":
    create_tables()
    print("Tablas creadas correctamente.")