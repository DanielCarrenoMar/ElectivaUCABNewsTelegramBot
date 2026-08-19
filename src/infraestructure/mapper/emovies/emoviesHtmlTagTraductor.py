import logging
from typing import Optional

# Traduce los slugs de las clases HTML (course_disciplinary_new-*, course_level-*,
# university_language-*) a los IDs de catálogo de la app (defaultValuesCatalog.py).
#
# La primera sección de cada mapa contiene los slugs encontrados en los archivos
# disciplinary.txt, language.txt y level.txt; la segunda completa el resto del
# catálogo de la app con la misma estructura (slug normalizado del nombre).

_HTML_TAG_TO_APP_COURSE_LEVELS: dict[str, Optional[int]] = {
    # Slugs de level.txt
    "posgrado": 3,  # Posgrado/Postgraduate
    "pregrado": 4,  # Pregrado/Undergraduate
    "tecnico-tecnologico-superior": 5,  # Técnico-Tecnológico Superior/ Technical-Technological
    # Resto del catálogo de la app
    "doctorado": 1,  # Doctorado/Doctorate
    "formacion-continua": 2,  # Formación continua/ Continuous training
}

_HTML_TAG_TO_APP_DISCIPLINARY_FIELDS: dict[str, Optional[int]] = {
    # Slugs de disciplinary.txt
    "ingenierias": 17,  # Ingenierías
    "gestion-empresarial": 7,  # Administración de empresas
    "ciencias-administrativas": 2,  # Ciencias administrativas
    "arquitectura-y-diseno": 4,  # Arquitectura y diseño
    "ciencias-economico-administrativas": 12,  # Ciencias económico-administrativas
    "ciencias-sociales-y-humanidades": 45,  # Ciencias sociales y Humanidades
    "negocios-internacionales": None,  # Sin equivalente en el catálogo de la app
    "ciencias-de-la-salud": 20,  # Ciencias de la salud
    "educacion-y-pedagogia": 15,  # Educación y pedagogía
    "psicologia": 43,  # Psicología
    "ciencias-biologicas": 6,  # Ciencias Biológicas
    # Resto del catálogo de la app
    "contabilidad": 1,  # Contabilidad
    "agronomia-y-estudios-de-la-tierra": 3,  # Agronomía y estudios de la tierra
    "artes": 5,  # Artes
    "ingenieria-civil": 8,  # Ingeniería Civil
    "ciencias-de-la-comunicacion": 9,  # Ciencias de la comunicación
    "comunicacion": 10,  # Comunicación
    "odontologia": 11,  # Odontología
    "economia": 13,  # Economía
    "educacion": 14,  # Educación
    "ingenieria-electronica": 16,  # Ingeniería Electrónica
    "finanzas": 18,  # Finanzas
    "artes-graficas-y-escenicas": 19,  # Artes gráficas y escénicas
    "historia": 21,  # Historia
    "idiomas": 22,  # Idiomas
    "derecho": 23,  # Derecho
    "literatura": 24,  # Literatura
    "macroeconomia": 25,  # Macroeconomía
    "mercadotecnia-y-publicidad": 26,  # Mercadotecnia y publicidad
    "matematicas": 27,  # Matemáticas
    "microeconomia": 28,  # Microeconomía
    "musica": 29,  # Música
    "nutricion": 30,  # Nutrición
    "salud-y-proteccion-laboral": 31,  # Salud y protección laboral
    "otra-arte": 32,  # Otra Arte
    "otra-ciencia-de-la-comunicacion": 33,  # Otra Ciencia de la comunicación
    "otra-ciencia-economico-administrativa": 34,  # Otra Ciencia económico-administrativa
    "otra-educacion-y-pedagogia": 35,  # Otra Educación y pedagogía
    "otra-ciencia-de-la-salud": 36,  # Otra Ciencia de la salud
    "otra-ciencia-social-o-humanidad": 37,  # Otra Ciencia social o humanidad
    "pedagogia": 38,  # Pedagogía
    "filosofia-y-etica": 39,  # Filosofía y ética
    "fisica": 40,  # Física
    "artes-plasticas": 41,  # Artes plásticas
    "ciencias-politicas": 42,  # Ciencias politicas
    "servicios": 44,  # Servicios
    "sociologia": 46,  # Sociología
    "deportes": 47,  # Deportes
    "veterinaria-y-zootecnia": 48,  # Veterinaria y zootecnia
}

_HTML_TAG_TO_APP_LANGUAGES: dict[str, Optional[int]] = {
    # Slugs de language.txt
    "espanol": 1,  # Español
    # Resto del catálogo de la app
    "frances": 2,  # Francés
    "ingles": 3,  # Ingles
    "pt": 5,  # Portugués
    "otro": 6,  # Otro
}

_HTML_TAG_TO_APP_MAP: dict[str, dict[str, Optional[int]]] = {
    "languages": _HTML_TAG_TO_APP_LANGUAGES,
    "course_levels": _HTML_TAG_TO_APP_COURSE_LEVELS,
    "disciplinary_fields": _HTML_TAG_TO_APP_DISCIPLINARY_FIELDS,
}

def emoviesHtmlTagToAppIdCatalog(catalog: str, htmlTag: Optional[str]) -> Optional[int]:
    if htmlTag is None:
        return None

    appId = _HTML_TAG_TO_APP_MAP.get(catalog, {}).get(htmlTag)
    if appId is None:
        logging.debug(
            "Tag HTML '%s' no encontrado en catálogo '%s'",
            htmlTag,
            catalog,
        )
        return None

    return appId