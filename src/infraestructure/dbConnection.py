import os
import time

import psycopg
import psycopg.errors
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

# El bot habla con dos bases distintas: DB_URL guarda las suscripciones y los
# filtros de cada chat, COURSES_DB_URL guarda el catálogo de cursos y es de solo
# lectura. Cada variable tiene su propia conexión reutilizable.
_connections: dict[str, psycopg.Connection] = {}

DB_CONNECTION_RETRY_DELAY_SECONDS = float(os.getenv("DB_CONNECTION_RETRY_DELAY_SECONDS", "2"))
DB_CONNECTION_MAX_RETRIES = int(os.getenv("DB_CONNECTION_MAX_RETRIES", "3"))


def _connection_for(urlVariable: str) -> psycopg.Connection:
    url = os.getenv(urlVariable)
    if not url:
        raise RuntimeError(f"Falta variable de entorno {urlVariable}")

    connection = _connections.get(urlVariable)
    last_error = None
    for attempt in range(DB_CONNECTION_MAX_RETRIES + 1):
        try:
            if connection is None or connection.closed:
                connection = psycopg.connect(url, autocommit=True, row_factory=dict_row)
            else:
                connection.execute("SELECT 1")
            _connections[urlVariable] = connection
            return connection
        except (psycopg.OperationalError, psycopg.errors.OperationalError) as error:
            last_error = error
            connection = None
            if attempt < DB_CONNECTION_MAX_RETRIES:
                time.sleep(DB_CONNECTION_RETRY_DELAY_SECONDS)

    _connections[urlVariable] = None

    if last_error is not None:
        raise last_error

    raise RuntimeError(f"No se pudo conectar a la base de datos de {urlVariable}")


def get_db_connection() -> psycopg.Connection:
    """Conexión a la base de suscripciones y filtros de chat (lectura y escritura)."""
    return _connection_for("DB_URL")


def get_courses_db_connection() -> psycopg.Connection:
    """Conexión al catálogo de cursos, propiedad de otro sistema. Solo lectura."""
    return _connection_for("COURSES_DB_URL")