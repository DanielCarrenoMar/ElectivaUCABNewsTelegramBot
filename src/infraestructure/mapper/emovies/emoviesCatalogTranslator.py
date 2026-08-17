import logging
from typing import Optional

from psycopg import sql

from src.infraestructure.dbConnection import get_db_connection
from infraestructure.mapper.emovies.emoviesCatalogData import EMOVIES_CATALOG_MAP


class EmoviesCatalogTranslator:
    CATALOG_TABLES = {
        "countries": ("countries", "country"),
        "universities": ("universities", "university"),
        "languages": ("languages", "language"),
        "course_levels": ("course_levels", "course_level"),
        "disciplinary_fields": ("disciplinary_fields", "disciplinary_field"),
    }

    def __init__(self):
        self._valueToId: dict[str, dict[str, int]] = {}
        self._idToValue: dict[str, dict[int, str]] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return

        connection = get_db_connection()
        for catalog, (table, value_column) in self.CATALOG_TABLES.items():
            valueToId: dict[str, int] = {}
            idToValue: dict[int, str] = {}
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        "SELECT id, BTRIM({value_col}) AS {value_col} FROM {table}"
                    ).format(
                        value_col=sql.Identifier(value_column),
                        table=sql.Identifier(table),
                    )
                )
                rows = cursor.fetchall()

            for row in rows:
                value = row[value_column]
                dbId = row["id"]
                valueToId[value] = dbId
                idToValue[dbId] = value

            self._valueToId[catalog] = valueToId
            self._idToValue[catalog] = idToValue
            logging.info("Catálogo '%s' cargado: %d valores", catalog, len(rows))

        self._loaded = True

    def codeToDbId(self, catalog: str, emoviesCode: Optional[str]) -> Optional[int]:
        self._load()

        if not isinstance(emoviesCode, str) or not emoviesCode.isdigit():
            logging.debug(
                "Código eMOVIES no numérico para '%s': %r",
                catalog,
                emoviesCode,
            )
            return None

        value = EMOVIES_CATALOG_MAP.get(catalog, {}).get(emoviesCode)
        if value is None:
            logging.debug("Sin valor de catálogo para código '%s' en '%s'", emoviesCode, catalog)
            return None

        dbId = self._valueToId.get(catalog, {}).get(value)
        if dbId is None:
            logging.debug(
                "Código eMOVIES '%s' ('%s') no encontrado en BD catálogo '%s'",
                emoviesCode,
                value,
                catalog,
            )
            return None

        return dbId

    def dbIdToName(self, catalog: str, dbId: Optional[int]) -> Optional[str]:
        self._load()

        if dbId is None:
            return None

        return self._idToValue.get(catalog, {}).get(dbId)

    def idToNameMaps(self) -> dict[str, dict[int, str]]:
        self._load()

        return {catalog: dict(mapping) for catalog, mapping in self._idToValue.items()}