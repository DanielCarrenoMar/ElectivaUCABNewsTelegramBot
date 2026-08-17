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

_EMOVIES_TO_APP_UNIVERSITIES: dict[int, int] = {
    98250: 1,    # Benemérita Universidad Autónoma de Puebla
    825: 2,      # Centro Paula Souza
    946: 3,      # Corporación Tecnológica de Bogotá
    77270: 4,    # Corporación Unificada Nacional de Educación Superior - CUN
    41236: 5,    # Corporación Universidad de la Costa
    74459: 6,    # Corporación Universitaria Iberoamericana - IBERO
    898: 7,      # Corporación Universitaria Minuto de Dios
    10498: 8,    # Corporación Universitaria Remington
    18359: 9,    # Corporación Universitaria Unitec
    34358: 10,   # ESCUELA SUPERIOR POLITÉCNICA DE CHIMBORAZO
    982: 11,     # Escuela Superior Politécnica del Litoral
    54219: 12,   # Faculdade Frassinetti do Recife - FAFIRE
    16249: 13,   # Fundação Santo André
    774: 14,     # Fundación H.A. Barceló
    73280: 15,   # Fundación Universidad de América
    872: 16,     # Fundación Universitaria Católica del Norte
    8254: 17,    # Fundación Universitaria CEIPA
    893: 18,     # Fundación Universitaria de Ciencias de la Salud
    931: 19,     # Fundación Universitaria del Área Andina
    67093: 20,   # Fundación Universitaria Juan N. Corpas
    90220: 21,   # Fundación Universitaria Los Libertadores
    24928: 22,   # Institución B
    7886: 23,    # Institución Universitaria Esumer
    977: 24,     # Institución Universitaria ITM
    967: 25,     # Institución Universitaria Pascual Bravo
    16801: 26,   # Instituto Politécnico Nacional
    10008: 27,   # Instituto Superior de Formación Docente Salomé Ureña (ISFODOSU)
    1080: 28,    # Instituto Tecnológico de las Américas
    64369: 29,   # Instituto Universitario American College
    8127: 30,    # Justice Institute of British Columbia
    840: 31,     # Lakehead University
    95367: 32,   # Otra IES
    1085: 33,    # Pontificia Universidad Católica Madre y Maestra
    820: 34,     # Pontifícia Universidade Católica do Rio Grande do Sul
    100105: 35,  # Universidad Abierta para Adultos
    22677: 36,   # Universidad Amazónica de Pando
    69498: 37,   # Universidad Anáhuac Cancún
    1022: 38,    # Universidad Anáhuac México
    1040: 39,    # Universidad Anáhuac Xalapa
    14528: 40,   # UNIVERSIDAD ANDINA DEL CUSCO
    35518: 41,   # UNIVERSIDAD ANDRÉS BELLO
    930: 42,     # Universidad Antonio Nariño
    1091: 43,    # Universidad Apec
    10264: 44,   # UNIVERSIDAD ARTURO PRAT
    75427: 45,   # Universidad Autónoma de Baja California
    1012: 46,    # Universidad Autónoma de Chiapas
    14146: 47,   # UNIVERSIDAD AUTÓNOMA DE CHIHUAHUA
    854: 48,     # Universidad Autónoma de Chile
    1045: 49,    # Universidad Autónoma de Ciudad Juárez
    1027: 50,    # Universidad Autónoma de Guerrero
    1017: 51,    # Universidad Autónoma de La Laguna
    907: 52,     # Universidad Autónoma de Occidente
    1059: 53,    # Universidad Autónoma de San Luis Potosí
    1060: 54,    # Universidad Autónoma de Tlaxcala
    1049: 55,    # Universidad Autónoma de Yucatán
    59363: 56,   # Universidad Bolivariana del Ecuador
    1101: 57,    # Universidad Católica Andrés Bello
    40696: 58,   # Universidad Católica de Colombia
    849: 59,     # Universidad Católica de la Santísima Concepción
    36603: 60,   # Universidad Católica de Santiago de Guayaquil
    845: 61,     # Universidad Católica de Temuco
    59591: 62,   # Universidad Católica del Cibao
    1090: 63,    # Universidad Católica Nordestana
    1096: 64,    # Universidad Católica Tecnológica de Barahona
    14578: 65,   # Universidad Central de Chile
    16792: 66,   # UNIVERSIDAD CENTRAL DEL ESTE
    92058: 67,   # UNIVERSIDAD CENTRAL DEL PARAGUAY
    89784: 68,   # UNIVERSIDAD CÉSAR VALLEJO
    1075: 69,    # Universidad Continental SAC
    903: 70,     # Universidad Cooperativa de Colombia
    90002: 71,   # Universidad Cristóbal Colón
    941: 72,     # Universidad de Caldas
    936: 73,     # Universidad de Ciencias Aplicadas y Ambientales
    51760: 74,   # Universidad de Ciencias y Humanidades
    14610: 75,   # Universidad de Colima
    14175: 76,   # Universidad de Concepción
    888: 77,     # Universidad de Córboda
    1007: 78,    # Universidad de Cuenca
    22634: 79,   # Universidad de Guadalajara
    24869: 80,   # Universidad de Guanajuato
    75449: 81,   # Universidad de Investigación de Tecnología Experimental Yachay
    7972: 82,    # Universidad de La Frontera
    25947: 83,   # UNIVERSIDAD DE LAS AMERICAS
    89149: 84,   # Universidad de las Artes
    89686: 85,   # UNIVERSIDAD DE LAS FUERZAS ARMADAS - ESPE
    73658: 86,   # Universidad de Lima
    857: 87,     # Universidad de Los Lagos
    9918: 88,    # Universidad de los Llanos
    862: 89,     # Universidad de Manizales
    1054: 90,    # Universidad de Monterrey
    784: 91,     # Universidad de Morón
    14561: 92,   # UNIVERSIDAD DE PLAYA ANCHA
    7469: 93,    # Universidad de Quintana Roo
    85997: 94,   # Universidad de San Buenaventura, Sede Bogotá
    10235: 95,   # Universidad de Santiago de Chile
    1032: 96,    # Universidad de Sonora
    19163: 97,   # Universidad de Valparaíso
    1002: 98,    # Universidad del Azuay
    10177: 99,   # Universidad del Bío-Bío
    10489: 100,  # Universidad del Claustro de Sor Juana
    63247: 101,  # Universidad del Magdalena
    62364: 102,  # Universidad del Pacífico
    52650: 103,  # Universidad del Rosario
    769: 104,    # Universidad del Salvador
    1037: 105,   # Universidad del Valle de Atemajac
    52933: 106,  # Universidad Doctor Andrés Bello
    972: 107,    # Universidad EAN
    987: 108,    # Universidad Ecotec
    957: 109,    # Universidad El Bosque
    101812: 110, # Universidad Estatal de Bolívar
    79847: 111,  # Universidad Estatal del Sur de Manabí
    72585: 112,  # Universidad Evangélica de El Salvador
    60953: 113,  # Universidad Franz Tamayo
    36432: 114,  # UNIVERSIDAD GASTÓN DACHARY
    66540: 115,  # Universidad Gerardo Barrios
    24240: 116,  # Universidad Iberoamericana (UNIBE)
    7191: 117,   # Universidad Iberoamericana Ciudad de México
    57049: 118,  # UNIVERSIDAD IBEROAMERICANA DE CIENCIA Y TECNOLOGÍA (UNICIT)
    962: 119,    # Universidad Industrial de Santander
    22653: 120,  # Universidad Internacional de Ciencia y Tecnología
    877: 121,    # Universidad La Gran Colombia
    59093: 122,  # Universidad La Salle Bajio
    911: 123,    # Universidad Libre
    818: 124,    # Universidad Mayor, Real y Pontificia de San Francisco Xavier de Chuquisaca
    10517: 125,  # Universidad Metropolitana - UNIMET
    21720: 126,  # UNIVERSIDAD MILITAR NUEVA GRANADA
    867: 127,    # Universidad Nacional Abierta y a Distancia
    803: 128,    # Universidad Nacional Arturo Jauretche
    14310: 129,  # Universidad Nacional de Córdoba
    14556: 130,  # Universidad Nacional de Cuyo
    789: 131,    # Universidad Nacional de Hurlingham
    19575: 132,  # UNIVERSIDAD NACIONAL DE LOJA
    808: 133,    # Universidad Nacional de Mar del Plata
    793: 134,    # Universidad Nacional de Río Negro
    90304: 135,  # Universidad Nacional de San Juan
    8234: 136,   # Universidad Nacional del Este
    8997: 137,   # Universidad Nacional del Litoral
    798: 138,    # Universidad Nacional del Nordeste
    779: 139,    # Universidad Nacional del Noroeste de la Provincia de Buenos Aires
    10145: 140,  # Universidad Nacional del Sur
    58196: 141,  # Universidad Particular de Especialidades Espíritu Santo
    45944: 142,  # Universidad Pedagógica de El Salvador "Dr. Luis Alonso Aparicio"
    952: 143,    # Universidad Piloto de Colombia
    83183: 144,  # Universidad Politécnica Estatal del Carchi
    992: 145,    # Universidad Politécnica Salesiana
    22835: 146,  # Universidad Privada Abierta Latinoamericana
    817: 147,    # Universidad Privada de Santa Cruz de la Sierra
    66346: 148,  # Universidad Privada del Este
    74774: 149,  # Universidad Privada del Norte
    813: 150,    # Universidad Privada del Valle
    8391: 151,   # Universidad Privada Domingo Savio
    23206: 152,  # Universidad Salvadoreña Alberto Masferrer
    75514: 153,  # UNIVERSIDAD SAN GREGORIO DE PORTOVIEJO
    916: 154,    # Universidad Santo Tomás, Seccional Bogotá
    921: 155,    # Universidad Santo Tomás, Seccional Bucaramanga
    926: 156,    # Universidad Santo Tomás, Seccional Medellín
    927: 157,    # Universidad Santo Tomás, Seccional Tunja
    928: 158,    # Universidad Santo Tomás, Seccional Villavicencio
    101682: 159, # Universidad SEK
    87788: 160,  # Universidad Técnica de Babahoyo
    76164: 161,  # Universidad Técnica de Machala
    997: 162,    # Universidad Técnica Particular de Loja
    882: 163,    # Universidad Tecnológica de Bolívar
    1065: 164,   # Universidad Tecnológica de Panamá
    52648: 165,  # Universidad Tecnológica de Pereira
    1070: 166,   # Universidad Tecnológica del Perú
    52235: 167,  # Universidad Tecnológica Privada de Santa Cruz - UTEPSA
    80507: 168,  # UNIVERSIDAD VASCO DE QUIROGA
    14559: 169,  # Universidad Veracruzana
    24992: 170,  # Universidade Alto Vale do Rio do Peixe - UNIARP
    22758: 171,  # Universidade Comunitária da Região de Chapecó
    25977: 172,  # Universidade da Região de Joinville - Univille
    830: 173,    # Universidade de Santa Cruz do Sul
    66348: 174,  # Universidade do Estado de Santa Catarina
    66356: 175,  # Universidade do Extremo Sul Catarinense
    835: 176,    # Universidade do Oeste de Santa Catarina
    77375: 177,  # Universidade do Planalto Catarinense - UNIPLAC
    66147: 178,  # UNIVERSIDADE DO VALE DO ITAJAÍ - UNIVALI
    8076: 179,   # Universidade Federal de Pernambuco / UFPE
    57585: 180,  # Universidade Federal de Rondonópolis - UFR
    52703: 181,  # Universidade Federal de Uberlândia
    84183: 182,  # Universidade Veiga de Almeida
    8098: 183,   # Université du Québec à Trois-Rivières
}

_EMOVIES_TO_APP_LANGUAGES: dict[int, int] = {
    48: 1,    # Español
    109: 2,   # Frances
    78: 3,    # Ingles
    24: 4     # Portugues
}

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