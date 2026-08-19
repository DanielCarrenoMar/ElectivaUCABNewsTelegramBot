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
    "negocios-internacionales": 62,  # Negocios Internacionales
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
    "biologia": 49,  # Biología
    "ciencias-exactas-y-naturales": 50,  # Ciencias exactas y naturales
    "enfermeria": 51,  # Enfermería
    "farmacia": 52,  # Farmacia
    "geografia": 53,  # Geografía
    "geologia": 54,  # Geología
    "hoteleria-y-turismo": 56,  # Hotelería y turismo
    "ingenieria-de-sistemas": 57,  # Ingeniería de Sistemas
    "ingenieria-electrica": 58,  # Ingeniería Eléctrica
    "ingenieria-industrial": 59,  # Ingeniería Industrial
    "ingenieria-mecanica": 60,  # Ingeniería Mecánica
    "medicina": 61,  # Medicina
    "otra-ciencia-administrativa": 63,  # Otra Ciencia administrativa
    "otra-ciencia-biologica": 64,  # Otra Ciencia Biológica
    "otra-ciencia-exacta-o-natural": 65,  # Otra Ciencia exacta o natural
    "otra-ingenieria": 66,  # Otra Ingeniería
    "periodismo": 67,  # Periodismo
    "quimica": 68,  # Química
    "religion-y-teologia": 69,  # Religión y teología
    "salud-infantil": 70,  # Salud infantil
    "terapia-y-rehabilitacion": 71,  # Terapia y rehabilitación
    "trabajo-social": 72,  # Trabajo Social
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