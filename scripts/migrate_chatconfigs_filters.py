"""Migra los filtros de `chatconfigs` de IDs enteros a claves naturales.

El bot era dueño de sus catálogos (países, universidades, idiomas, niveles y
áreas disciplinarias) y guardaba en cada filtro el INT de ese catálogo. Ahora el
catálogo vive en otra base de datos, con espacios de identificadores sin
relación, así que cada filtro debe guardar la clave natural del catálogo nuevo:

    uni_countries        -> country_iso_code      (countries.iso_code)
    course_university    -> course_university     (universities.name)
    uni_languages        -> course_language_code  (languages.code)
    course_levels        -> course_level_id       (academic_levels.id)
    disciplinary_field   -> disciplinary_field    (knowledge_areas.name)

Los catálogos viejos se leen de esta misma base (se eliminan más adelante) y se
resuelven contra la base del catálogo de cursos. Un valor que no resuelve se
convierte en NULL, es decir el filtro se abre a "cualquiera": el chat sigue
suscrito y puede recibir alguna notificación de más, nunca menos.

Uso:

    python -m scripts.migrate_chatconfigs_filters            # sobre chatconfigs
    python -m scripts.migrate_chatconfigs_filters chatconfigs_legacy

Es idempotente: si las columnas enteras ya no existen, no se toca nada y lo dice
explícitamente.
"""

import logging
import pathlib
import sys
import unicodedata
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.infraestructure.dbConnection import (  # noqa: E402  (sys.path antes del import)
    get_courses_db_connection,
    get_db_connection,
)

# Id de `course_levels` viejo -> `academic_levels.id` de la base nueva. No se
# puede resolver por nombre porque ambos catálogos nombran distinto
# ("Doctorado/Doctorate" vs "Doctorado") y las claves nuevas están en inglés.
COURSE_LEVEL_IDS = {
    1: "doctorate",
    2: "continuing_education",
    3: "postgraduate",
    4: "undergraduate",
    5: "technical_technological",
}

# Dimensión de filtro -> (columna vieja INT, columna nueva de texto)
FILTER_DIMENSIONS = [
    ("pais", "uni_countries", "country_iso_code"),
    ("universidad", "course_university", "course_university"),
    ("idioma", "uni_languages", "course_language_code"),
    ("nivel", "course_levels", "course_level_id"),
    ("area", "disciplinary_field", "disciplinary_field"),
]

# Catálogo viejo del que sale el nombre legible de cada valor perdido
OLD_VALUE_SOURCES = {
    "country_iso_code": ("countries", "country"),
    "course_university": ("universities", "university"),
    "course_language_code": ("languages", "language"),
    "course_level_id": ("course_levels", "course_level"),
    "disciplinary_field": ("disciplinary_fields", "disciplinary_field"),
}

OLD_INTEGER_COLUMNS = [old for _, old, _ in FILTER_DIMENSIONS]
NEW_TEXT_COLUMNS = [new for _, _, new in FILTER_DIMENSIONS]

READ_ROWS = """
SELECT id, lastrevision, is_subscribed, key_word,
       uni_countries, course_university, uni_languages,
       course_levels, disciplinary_field
FROM {table}
ORDER BY id
"""

UPSERT_ROW = """
INSERT INTO chatconfigs (
    id, lastrevision, is_subscribed, key_word,
    country_iso_code, course_university, course_language_code,
    course_level_id, disciplinary_field
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    lastrevision = EXCLUDED.lastrevision,
    is_subscribed = EXCLUDED.is_subscribed,
    key_word = EXCLUDED.key_word,
    country_iso_code = EXCLUDED.country_iso_code,
    course_university = EXCLUDED.course_university,
    course_language_code = EXCLUDED.course_language_code,
    course_level_id = EXCLUDED.course_level_id,
    disciplinary_field = EXCLUDED.disciplinary_field
"""


def normalize(text: str) -> str:
    """Normaliza un nombre de catálogo para comparar entre las dos bases.

    Descompone en NFKD, quita marcas diacríticas, pasa a minúsculas, colapsa el
    whitespace y quita el ruido de puntuación de los extremos.

    Se reimplementa aquí a propósito en vez de importar
    `mapper/ausjal/ausjalCatalogTranslator._normalize`: ese módulo desaparece
    en la limpieza del pipeline de scraping y esta migración debe seguir
    funcionando sin él.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    collapsed = " ".join(without_accents.lower().split())
    return collapsed.strip(" \t\n\r.,;:!?-_/\\\"'()[]{}|*")


class MigrationError(Exception):
    """Falla prevista de la migración: se reporta y se sale, sin traza."""


class AlreadyMigrated(Exception):
    """No hay nada que migrar: las columnas enteras ya no existen."""


def table_exists(cursor, table: str) -> bool:
    cursor.execute(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables"
        " WHERE table_schema = 'public' AND table_name = %s) AS exists",
        (table,),
    )
    # Las conexiones compartidas usan row_factory=dict_row.
    return cursor.fetchone()["exists"]


def columns_of(cursor, table: str) -> Dict[str, str]:
    cursor.execute(
        "SELECT column_name, data_type FROM information_schema.columns"
        " WHERE table_schema = 'public' AND table_name = %s",
        (table,),
    )
    return {row["column_name"]: row["data_type"] for row in cursor.fetchall()}


def old_integer_columns_present(columns: Dict[str, str]) -> List[str]:
    """Columnas viejas que todavía son INT.

    No basta con preguntar si el nombre existe: `course_university` y
    `disciplinary_field` se llaman igual en los dos esquemas, así que la única
    forma fiable de saber si la migración ya corrió es mirar el tipo.
    """
    return [column for column in OLD_INTEGER_COLUMNS if columns.get(column) == "integer"]


def old_catalog(cursor, table: str, value_column: str) -> Dict[int, str]:
    """Lee un catálogo viejo completo: id -> valor."""
    cursor.execute(f"SELECT id, {value_column} FROM {table}")
    return {row["id"]: row[value_column] for row in cursor.fetchall()}


def name_index(cursor, table: str, name_column: str, key_column: Optional[str] = None) -> Dict[str, object]:
    """Índice nombre normalizado -> clave natural del catálogo nuevo."""
    if key_column:
        cursor.execute(f"SELECT {key_column}, {name_column} FROM {table}")
        return {normalize(row[name_column]): row[key_column] for row in cursor.fetchall()}
    cursor.execute(f"SELECT {name_column} FROM {table}")
    return {normalize(row[name_column]): row[name_column] for row in cursor.fetchall()}


def by_name(catalog: Dict[int, str], target: Dict[str, object]) -> Dict[int, Optional[object]]:
    """Resuelve por nombre normalizado; sin coincidencia, None."""
    return {catalog_id: target.get(normalize(name)) for catalog_id, name in catalog.items()}


def build_resolution_maps() -> Dict[str, Dict[int, Optional[object]]]:
    """Arma los mapas id viejo -> clave natural del catálogo de cursos."""
    with get_db_connection().cursor() as cursor:
        old_countries = old_catalog(cursor, "countries", "country")
        old_universities = old_catalog(cursor, "universities", "university")
        old_fields = old_catalog(cursor, "disciplinary_fields", "disciplinary_field")
        old_levels = old_catalog(cursor, "course_levels", "course_level")
        old_languages = old_catalog(cursor, "languages", "language")

    with get_courses_db_connection().cursor() as cursor:
        new_countries = name_index(cursor, "countries", "name", key_column="iso_code")
        new_universities = name_index(cursor, "universities", "name")
        new_fields = name_index(cursor, "knowledge_areas", "name")
        new_levels = {row["id"] for row in cursor.execute("SELECT id FROM academic_levels").fetchall()}
        new_languages = {row["code"] for row in cursor.execute("SELECT code FROM languages").fetchall()}

    # Los códigos de idioma son los mismos strings que los ids viejos, así que
    # alcanza con validar que existan en la base nueva.
    level_map = {
        catalog_id: level_id
        for catalog_id in old_levels
        for level_id in [COURSE_LEVEL_IDS.get(catalog_id)]
        if level_id in new_levels
    }
    language_map = {
        catalog_id: code
        for catalog_id in old_languages
        for code in [str(catalog_id)]
        if code in new_languages
    }

    return {
        "country_iso_code": by_name(old_countries, new_countries),
        "course_university": by_name(old_universities, new_universities),
        "course_language_code": language_map,
        "course_level_id": level_map,
        "disciplinary_field": by_name(old_fields, new_fields),
    }


def old_value_label(cursor, table: str, value_column: str, value: int) -> str:
    """Nombre legible del valor viejo, para el reporte de pérdidas."""
    cursor.execute(f"SELECT {value_column} AS value FROM {table} WHERE id = %s", (value,))
    row = cursor.fetchone()
    return row["value"] if row else f"id {value} (sin fila en {table})"


def migrate(source_table: str = "chatconfigs") -> int:
    connection = get_db_connection()
    with connection.cursor() as cursor:
        if not table_exists(cursor, "chatconfigs"):
            raise MigrationError(
                "La tabla 'chatconfigs' no existe en la base de suscripciones. "
                "Córrela antes: python -m scripts.seed"
            )
        target_columns = columns_of(cursor, "chatconfigs")

        if not table_exists(cursor, source_table):
            raise MigrationError(
                f"La tabla '{source_table}' no existe: no hay filas de las que leer."
            )
        source_columns = columns_of(cursor, source_table)

    remaining_integers = old_integer_columns_present(source_columns)
    if not remaining_integers:
        raise AlreadyMigrated(source_table)

    if not [column for column in NEW_TEXT_COLUMNS if column in target_columns]:
        raise MigrationError(
            "La tabla 'chatconfigs' no tiene las columnas de texto nuevas "
            f"({', '.join(NEW_TEXT_COLUMNS)}). Crea el esquema antes: python -m scripts.seed"
        )

    maps = build_resolution_maps()
    resolved = {new_column: 0 for _, _, new_column in FILTER_DIMENSIONS}
    losses: List[Tuple[str, str, int]] = []
    migrated = 0

    with connection.cursor() as cursor:
        cursor.execute(READ_ROWS.format(table=source_table))
        rows = cursor.fetchall()

        for row in rows:
            values = []
            for _, old_column, new_column in FILTER_DIMENSIONS:
                old_value = row[old_column]
                if old_value is None:
                    values.append(None)
                    continue
                new_value = maps[new_column].get(old_value)
                if new_value is None:
                    table, value_column = OLD_VALUE_SOURCES[new_column]
                    losses.append((new_column, old_value_label(cursor, table, value_column, old_value), row["id"]))
                else:
                    resolved[new_column] += 1
                values.append(new_value)

            cursor.execute(
                UPSERT_ROW,
                (row["id"], row["lastrevision"], row["is_subscribed"], row["key_word"], *values),
            )
            migrated += 1

    print_report(migrated, resolved, losses)
    return migrated


def print_report(migrated: int, resolved: Dict[str, int], losses: List[Tuple[str, str, int]]) -> None:
    print()
    print("=" * 78)
    print(f"Migración de filtros de chatconfigs — {migrated} filas procesadas")
    print("=" * 78)
    print()
    print(f"{'dimensión':<14}{'columna nueva':<24}{'resueltos':>10}{'perdidos':>10}")
    for label, _, new_column in FILTER_DIMENSIONS:
        lost = sum(1 for loss in losses if loss[0] == new_column)
        print(f"{label:<14}{new_column:<24}{resolved[new_column]:>10}{lost:>10}")

    if not losses:
        print()
        print("Ningún filtro se perdió: todos los valores resolvieron en el catálogo nuevo.")
        print("=" * 78)
        return

    print()
    print("Valores que NO resolvieron (el filtro quedó en NULL = 'cualquiera'):")
    for label, _, new_column in FILTER_DIMENSIONS:
        for column, value, chat_id in losses:
            if column == new_column:
                print(f"  - [{label}] '{value}' -> chat {chat_id}")
    print()
    print("Los chats afectados pueden recibir notificaciones de más, no de menos.")
    print("=" * 78)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    source_table = sys.argv[1] if len(sys.argv) > 1 else "chatconfigs"
    try:
        migrate(source_table)
    except AlreadyMigrated as skip:
        print(
            f"No se aplicó nada: en '{skip.args[0]}' ninguna de las columnas de filtro "
            f"({', '.join(OLD_INTEGER_COLUMNS)}) sigue siendo INTEGER, así que los datos "
            "ya están en claves naturales. Los datos de 'chatconfigs' quedan intactos."
        )
        return 0
    except MigrationError as error:
        print(f"Migración no aplicada: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())