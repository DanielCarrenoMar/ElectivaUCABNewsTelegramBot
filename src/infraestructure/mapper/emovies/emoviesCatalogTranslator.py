import logging
from typing import Optional

_EMOVIES_TO_APP_COUNTRIES = {
        16: 1,  # Argentina
        17: 2,  # Bolivia
        43: 3,  # Brasil
        197: 4,  # Brazil
        6: 5,  # Canada
        18: 6,  # Chile
        19: 7,  # Colombia
        20: 8,  # Ecuador
        201: 9,  # El Salvador
        21: 10,  # Mexico
        199: 11,  # Nicaragua
        44: 12,  # Panamá
        194: 13,  # Paraguay
        22: 14,  # Peru
        45: 15,  # República Dominicana
        23: 16,  # Venezuela
    }

_EMOVIES_TO_APP_COURSE_LEVELS = {
    119: 1,  # Doctorado/Doctorate
    124: 2,  # Formación continua/ Continuous training
    79: 3,  # Posgrado/Postgraduate
    86: 4,  # Pregrado/Undergraduate
    112: 5,  # Técnico-Tecnológico Superior/ Technical-Technological
}

_EMOVIES_TO_APP_DISCIPLINARY_FIELDS = {
    220: 1,  # Administración de empresas
    262: 2,  # Agronomía y estudios de la tierra
    322: 3,  # Arquitectura y diseño
    292: 4,  # Artes
    294: 5,  # Artes gráficas y escénicas
    296: 6,  # Artes plásticas
    326: 7,  # Biología
    218: 8,  # Ciencias administrativas
    260: 9,  # Ciencias Biológicas
    284: 10,  # Ciencias de la comunicación
    238: 11,  # Ciencias de la salud
    208: 12,  # Ciencias económico-administrativas
    324: 13,  # Ciencias exactas y naturales
    304: 14,  # Ciencias politicas
    302: 15,  # Ciencias sociales y Humanidades
    288: 16,  # Comunicación
    222: 17,  # Contabilidad
    342: 18,  # Deportes
    306: 19,  # Derecho
    210: 20,  # Economía
    344: 21,  # Educación
    340: 22,  # Educación y pedagogía
    240: 23,  # Enfermería
    242: 24,  # Farmacia
    308: 25,  # Filosofía y ética
    224: 26,  # Finanzas
    328: 27,  # Física
    330: 28,  # Geografía
    332: 29,  # Geología
    226: 30,  # Gestión empresarial
    310: 31,  # Historia
    228: 32,  # Hotelería y turismo
    346: 33,  # Idiomas
    270: 34,  # Ingeniería Civil
    280: 35,  # Ingeniería de Sistemas
    272: 36,  # Ingeniería Eléctrica
    274: 37,  # Ingeniería Electrónica
    276: 38,  # Ingeniería Industrial
    278: 39,  # Ingeniería Mecánica
    268: 40,  # Ingenierías
    312: 41,  # Literatura
    212: 42,  # Macroeconomía
    334: 43,  # Matemáticas
    244: 44,  # Medicina
    230: 45,  # Mercadotecnia y publicidad
    298: 46,  # Música
    232: 47,  # Negocios Internacionales
    246: 48,  # Nutrición
    248: 49,  # Odontología
    300: 50,  # Otra Arte
    236: 51,  # Otra Ciencia administrativa
    266: 52,  # Otra Ciencia Biológica
    290: 53,  # Otra Ciencia de la comunicación
    258: 54,  # Otra Ciencia de la salud
    216: 55,  # Otra Ciencia económico-administrativa
    338: 56,  # Otra Ciencia exacta o natural
    320: 57,  # Otra Ciencia social o humanidad
    350: 58,  # Otra Educación y pedagogía
    282: 59,  # Otra Ingeniería
    348: 60,  # Pedagogía
    286: 61,  # Periodismo
    250: 62,  # Psicología
    336: 63,  # Química
    314: 64,  # Religión y teología
    254: 65,  # Salud infantil
    252: 66,  # Salud y protección laboral
    234: 67,  # Servicios
    316: 68,  # Sociología
    256: 69,  # Terapia y rehabilitación
    318: 70,  # Trabajo Social
    264: 71,  # Veterinaria y zootecnia
}

_EMOVIES_TO_APP_UNIVERSITIES: dict[int, int] = {}

_EMOVIES_TO_APP_LANGUAGES: dict[int, int] = {}

_EMOVIES_TO_APP_MAP: dict[str, dict[int, int]] = {
    "countries": _EMOVIES_TO_APP_COUNTRIES,
    "universities": _EMOVIES_TO_APP_UNIVERSITIES,
    "languages": _EMOVIES_TO_APP_LANGUAGES,
    "course_levels": _EMOVIES_TO_APP_COURSE_LEVELS,
    "disciplinary_fields": _EMOVIES_TO_APP_DISCIPLINARY_FIELDS,
}

def emoviesIdCatalogToAppIdCatalog(self, catalog: str, emoviesCode: Optional[int]) -> Optional[int]:
    global _EMOVIES_TO_APP_MAP

    if emoviesCode is None:
        return None

    appId = self._EMOVIES_TO_APP_MAP.get(catalog, {}).get(emoviesCode)
    if appId is None:
        logging.debug(
            "Código _EMOVIES '%s' no encontrado en catálogo '%s'",
            emoviesCode,
            catalog,
        )
        return None

    return appId