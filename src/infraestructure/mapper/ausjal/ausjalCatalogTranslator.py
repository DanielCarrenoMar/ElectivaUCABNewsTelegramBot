import logging
import re
import unicodedata
from typing import Optional


def _normalize(text: str) -> str:
    """Normaliza texto para usar como clave de catálogo.

    Quita acentos (NFKD), pasa a minúsculas y colapsa el whitespace.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_accents.lower().split())


_AUSJAL_TO_APP_COUNTRIES = {
    "argentina": 1,  # Argentina
    "brasil": 3,  # Brasil
    "ecuador": 8,  # Ecuador
    "el salvador": 9,  # El Salvador
    "mexico": 10,  # Mexico
    "venezuela": 16,  # Venezuela
    "españa": 17,  # España
}

_AUSJAL_TO_APP_COURSE_LEVELS = {
    "doctorado": 1,  # Doctorado/Doctorate
    "posgrado": 3,  # Posgrado/Postgraduate
    "pregrado": 4,  # Pregrado/Undergraduate
}

_AUSJAL_TO_APP_DISCIPLINARY_FIELDS = {
    "administracion de empresas": 7,  # Administración de empresas
    "ciencias de la salud": 20,  # Ciencias de la salud
    "derecho": 23,  # Derecho
    "educacion": 14,  # Educación
    "psicologia": 43,  # Psicología
}

# Las universidades AUSJAL aún no existen en el catálogo de la app
# (APP_UNIVERSITIES no contiene ninguna universidad AUSJAL actualmente),
# así que no hay equivalencias que mapear.
_AUSJAL_TO_APP_UNIVERSITIES: dict[str, int] = {}

_AUSJAL_TO_APP_LANGUAGES = {
    "espanol": 1,  # Español
    "ingles": 3,  # Ingles
    "portugues": 5,  # Portugués
}

_AUSJAL_TO_APP_MAP: dict[str, dict[str, int]] = {
    "countries": _AUSJAL_TO_APP_COUNTRIES,
    "universities": _AUSJAL_TO_APP_UNIVERSITIES,
    "languages": _AUSJAL_TO_APP_LANGUAGES,
    "course_levels": _AUSJAL_TO_APP_COURSE_LEVELS,
    "disciplinary_fields": _AUSJAL_TO_APP_DISCIPLINARY_FIELDS,
}


def ausjalTextToAppIdCatalog(catalog: str, text: Optional[str]) -> Optional[int]:
    if text is None:
        return None

    normalized = _normalize(text)
    appId = _AUSJAL_TO_APP_MAP.get(catalog, {}).get(normalized)
    if appId is None:
        logging.debug(
            "Texto AUSJAL '%s' no encontrado en catálogo '%s'",
            text,
            catalog,
        )
        return None

    return appId