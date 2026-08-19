import logging
import os
import time

import psycopg
import psycopg.errors
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

if not os.getenv("DB_URL"):
    raise RuntimeError("Falta variable de entorno DB_URL")

_databaseConnection = None
DB_CONNECTION_RETRY_DELAY_SECONDS = float(os.getenv("DB_CONNECTION_RETRY_DELAY_SECONDS", "2"))
DB_CONNECTION_MAX_RETRIES = int(os.getenv("DB_CONNECTION_MAX_RETRIES", "3"))


def get_db_connection():
    global _databaseConnection

    last_error = None
    for attempt in range(DB_CONNECTION_MAX_RETRIES + 1):
        try:
            if _databaseConnection is None or _databaseConnection.closed:
                _databaseConnection = psycopg.connect(
                    os.getenv("DB_URL"),
                    autocommit=True,
                    row_factory=dict_row,
                )
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