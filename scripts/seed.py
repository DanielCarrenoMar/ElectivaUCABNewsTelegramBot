import logging
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("DB_URL"):
    raise RuntimeError("Falta variable de entorno DB_URL")

# El catálogo de cursos y sus catálogos (países, universidades, idiomas, niveles,
# áreas disciplinarias) viven en otra base de datos y son propiedad de otro
# sistema: esta base solo guarda las suscripciones y los filtros de cada chat.
#
# Por esa razón los filtros ya no son INT con foreign key a catálogos propios,
# sino las claves naturales del catálogo externo, y no existe forma de declarar
# una foreign key entre bases distintas.
CREATE_CHAT_CONFIGS_TABLE = """
CREATE TABLE IF NOT EXISTS chatconfigs (
    id BIGINT PRIMARY KEY,
    lastrevision TIMESTAMPTZ DEFAULT now(),
    is_subscribed BOOLEAN NOT NULL DEFAULT TRUE,
    country_iso_code VARCHAR(2),
    course_university VARCHAR(150),
    course_language_code VARCHAR(5),
    course_level_id VARCHAR(50),
    disciplinary_field VARCHAR(100),
    key_word VARCHAR(50)
)
"""

# La búsqueda por palabra clave corre en Python sobre los cursos de la base
# externa, así que aquí no se necesita la extensión pg_trgm ni ningún índice
# trigram: chatconfigs solo guarda la palabra, nunca la busca.


def create_tables():
    with psycopg.connect(os.getenv("DB_URL"), autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_CHAT_CONFIGS_TABLE)
            logging.info("Seed: tabla 'chatconfigs' verificada")


if __name__ == "__main__":
    create_tables()
    print("Tablas creadas correctamente.")