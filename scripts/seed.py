import os

import psycopg
from dotenv import load_dotenv

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
    lastrevision DATE,
    uni_countries INT REFERENCES countries(id),
    disciplinary_field INT REFERENCES disciplinary_fields(id),
    course_university INT REFERENCES universities(id),
    uni_languages INT REFERENCES languages(id),
    course_levels INT REFERENCES course_levels(id),
    key_word CHAR(50)
)
"""


def create_tables():
    with psycopg.connect(os.getenv("DB_URL"), autocommit=True) as connection:
        with connection.cursor() as cursor:
            for table, value_column in CATALOG_TABLES.items():
                cursor.execute(CREATE_CATALOG_TABLE.format(table=table, value_column=value_column))
            cursor.execute(CREATE_CHAT_CONFIGS_TABLE)


if __name__ == "__main__":
    create_tables()
    print("Tablas creadas correctamente.")