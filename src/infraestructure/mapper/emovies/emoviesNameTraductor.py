import logging
from typing import Optional

# Traduce los nombres de universidades (los que aparecen en
# defaultValuesCatalog.py) a los IDs de catálogo de la app.
#
# Las claves están en minúsculas para que la comparación sea insensible
# a mayúsculas/minúsculas (el nombre puede llegar del scrapeo con otro
# formato, p. ej. todo en mayúsculas); el comentario muestra el nombre
# original del catálogo.

_NAME_TO_APP_UNIVERSITIES: dict[str, Optional[int]] = {
    "benemérita universidad autónoma de puebla": 1,  # Benemérita Universidad Autónoma de Puebla
    "centro paula souza": 2,  # Centro Paula Souza
    "corporación tecnológica de bogotá": 3,  # Corporación Tecnológica de Bogotá
    "corporación unificada nacional de educación superior - cun": 4,  # Corporación Unificada Nacional de Educación Superior - CUN
    "corporación universidad de la costa": 5,  # Corporación Universidad de la Costa
    "corporación universitaria iberoamericana - ibero": 6,  # Corporación Universitaria Iberoamericana - IBERO
    "corporación universitaria minuto de dios": 7,  # Corporación Universitaria Minuto de Dios
    "corporación universitaria remington": 8,  # Corporación Universitaria Remington
    "corporación universitaria unitec": 9,  # Corporación Universitaria Unitec
    "escuela superior politécnica de chimborazo": 10,  # ESCUELA SUPERIOR POLITÉCNICA DE CHIMBORAZO
    "escuela superior politécnica del litoral": 11,  # Escuela Superior Politécnica del Litoral
    "faculdade frassinetti do recife - fafire": 12,  # Faculdade Frassinetti do Recife - FAFIRE
    "fundação santo andré": 13,  # Fundação Santo André
    "fundación h.a. barceló": 14,  # Fundación H.A. Barceló
    "fundación universidad de américa": 15,  # Fundación Universidad de América
    "fundación universitaria católica del norte": 16,  # Fundación Universitaria Católica del Norte
    "fundación universitaria ceipa": 17,  # Fundación Universitaria CEIPA
    "fundación universitaria de ciencias de la salud": 18,  # Fundación Universitaria de Ciencias de la Salud
    "fundación universitaria del área andina": 19,  # Fundación Universitaria del Área Andina
    "fundación universitaria juan n. corpas": 20,  # Fundación Universitaria Juan N. Corpas
    "fundación universitaria los libertadores": 21,  # Fundación Universitaria Los Libertadores
    "institución b": 22,  # Institución B
    "institución universitaria esumer": 23,  # Institución Universitaria Esumer
    "institución universitaria itm": 24,  # Institución Universitaria ITM
    "institución universitaria pascual bravo": 25,  # Institución Universitaria Pascual Bravo
    "instituto politécnico nacional": 26,  # Instituto Politécnico Nacional
    "instituto superior de formación docente salomé ureña (isfodosu)": 27,  # Instituto Superior de Formación Docente Salomé Ureña (ISFODOSU)
    "instituto tecnológico de las américas": 28,  # Instituto Tecnológico de las Américas
    "instituto universitario american college": 29,  # Instituto Universitario American College
    "justice institute of british columbia": 30,  # Justice Institute of British Columbia
    "lakehead university": 31,  # Lakehead University
    "otra ies": 32,  # Otra IES
    "pontificia universidad católica madre y maestra": 33,  # Pontificia Universidad Católica Madre y Maestra
    "pontifícia universidade católica do rio grande do sul": 34,  # Pontifícia Universidade Católica do Rio Grande do Sul
    "universidad abierta para adultos": 35,  # Universidad Abierta para Adultos
    "universidad amazónica de pando": 36,  # Universidad Amazónica de Pando
    "universidad anáhuac cancún": 37,  # Universidad Anáhuac Cancún
    "universidad anáhuac méxico": 38,  # Universidad Anáhuac México
    "universidad anáhuac xalapa": 39,  # Universidad Anáhuac Xalapa
    "universidad andina del cusco": 40,  # UNIVERSIDAD ANDINA DEL CUSCO
    "universidad andrés bello": 41,  # UNIVERSIDAD ANDRÉS BELLO
    "universidad antonio nariño": 42,  # Universidad Antonio Nariño
    "universidad apec": 43,  # Universidad Apec
    "universidad arturo prat": 44,  # UNIVERSIDAD ARTURO PRAT
    "universidad autónoma de baja california": 45,  # Universidad Autónoma de Baja California
    "universidad autónoma de chiapas": 46,  # Universidad Autónoma de Chiapas
    "universidad autónoma de chihuahua": 47,  # UNIVERSIDAD AUTÓNOMA DE CHIHUAHUA
    "universidad autónoma de chile": 48,  # Universidad Autónoma de Chile
    "universidad autónoma de ciudad juárez": 49,  # Universidad Autónoma de Ciudad Juárez
    "universidad autónoma de guerrero": 50,  # Universidad Autónoma de Guerrero
    "universidad autónoma de la laguna": 51,  # Universidad Autónoma de La Laguna
    "universidad autónoma de occidente": 52,  # Universidad Autónoma de Occidente
    "universidad autónoma de san luis potosí": 53,  # Universidad Autónoma de San Luis Potosí
    "universidad autónoma de tlaxcala": 54,  # Universidad Autónoma de Tlaxcala
    "universidad autónoma de yucatán": 55,  # Universidad Autónoma de Yucatán
    "universidad bolivariana del ecuador": 56,  # Universidad Bolivariana del Ecuador
    "universidad católica andrés bello": 57,  # Universidad Católica Andrés Bello
    "universidad católica de colombia": 58,  # Universidad Católica de Colombia
    "universidad católica de la santísima concepción": 59,  # Universidad Católica de la Santísima Concepción
    "universidad católica de santiago de guayaquil": 60,  # Universidad Católica de Santiago de Guayaquil
    "universidad católica de temuco": 61,  # Universidad Católica de Temuco
    "universidad católica del cibao": 62,  # Universidad Católica del Cibao
    "universidad católica nordestana": 63,  # Universidad Católica Nordestana
    "universidad católica tecnológica de barahona": 64,  # Universidad Católica Tecnológica de Barahona
    "universidad central de chile": 65,  # Universidad Central de Chile
    "universidad central del este": 66,  # UNIVERSIDAD CENTRAL DEL ESTE
    "universidad central del paraguay": 67,  # UNIVERSIDAD CENTRAL DEL PARAGUAY
    "universidad césar vallejo": 68,  # UNIVERSIDAD CÉSAR VALLEJO
    "universidad continental sac": 69,  # Universidad Continental SAC
    "universidad cooperativa de colombia": 70,  # Universidad Cooperativa de Colombia
    "universidad cristóbal colón": 71,  # Universidad Cristóbal Colón
    "universidad de caldas": 72,  # Universidad de Caldas
    "universidad de ciencias aplicadas y ambientales": 73,  # Universidad de Ciencias Aplicadas y Ambientales
    "universidad de ciencias y humanidades": 74,  # Universidad de Ciencias y Humanidades
    "universidad de colima": 75,  # Universidad de Colima
    "universidad de concepción": 76,  # Universidad de Concepción
    "universidad de córboda": 77,  # Universidad de Córboda
    "universidad de cuenca": 78,  # Universidad de Cuenca
    "universidad de guadalajara": 79,  # Universidad de Guadalajara
    "universidad de guanajuato": 80,  # Universidad de Guanajuato
    "universidad de investigación de tecnología experimental yachay": 81,  # Universidad de Investigación de Tecnología Experimental Yachay
    "universidad de la frontera": 82,  # Universidad de La Frontera
    "universidad de las americas": 83,  # UNIVERSIDAD DE LAS AMERICAS
    "universidad de las artes": 84,  # Universidad de las Artes
    "universidad de las fuerzas armadas - espe": 85,  # UNIVERSIDAD DE LAS FUERZAS ARMADAS - ESPE
    "universidad de lima": 86,  # Universidad de Lima
    "universidad de los lagos": 87,  # Universidad de Los Lagos
    "universidad de los llanos": 88,  # Universidad de los Llanos
    "universidad de manizales": 89,  # Universidad de Manizales
    "universidad de monterrey": 90,  # Universidad de Monterrey
    "universidad de morón": 91,  # Universidad de Morón
    "universidad de playa ancha": 92,  # UNIVERSIDAD DE PLAYA ANCHA
    "universidad de quintana roo": 93,  # Universidad de Quintana Roo
    "universidad de san buenaventura, sede bogotá": 94,  # Universidad de San Buenaventura, Sede Bogotá
    "universidad de santiago de chile": 95,  # Universidad de Santiago de Chile
    "universidad de sonora": 96,  # Universidad de Sonora
    "universidad de valparaíso": 97,  # Universidad de Valparaíso
    "universidad del azuay": 98,  # Universidad del Azuay
    "universidad del bío-bío": 99,  # Universidad del Bío-Bío
    "universidad del claustro de sor juana": 100,  # Universidad del Claustro de Sor Juana
    "universidad del magdalena": 101,  # Universidad del Magdalena
    "universidad del pacífico": 102,  # Universidad del Pacífico
    "universidad del rosario": 103,  # Universidad del Rosario
    "universidad del salvador": 104,  # Universidad del Salvador
    "universidad del valle de atemajac": 105,  # Universidad del Valle de Atemajac
    "universidad doctor andrés bello": 106,  # Universidad Doctor Andrés Bello
    "universidad ean": 107,  # Universidad EAN
    "universidad ecotec": 108,  # Universidad Ecotec
    "universidad el bosque": 109,  # Universidad El Bosque
    "universidad estatal de bolívar": 110,  # Universidad Estatal de Bolívar
    "universidad estatal del sur de manabí": 111,  # Universidad Estatal del Sur de Manabí
    "universidad evangélica de el salvador": 112,  # Universidad Evangélica de El Salvador
    "universidad franz tamayo": 113,  # Universidad Franz Tamayo
    "universidad gastón dachary": 114,  # UNIVERSIDAD GASTÓN DACHARY
    "universidad gerardo barrios": 115,  # Universidad Gerardo Barrios
    "universidad iberoamericana (unibe)": 116,  # Universidad Iberoamericana (UNIBE)
    "universidad iberoamericana ciudad de méxico": 117,  # Universidad Iberoamericana Ciudad de México
    "universidad iberoamericana de ciencia y tecnología (unicit)": 118,  # UNIVERSIDAD IBEROAMERICANA DE CIENCIA Y TECNOLOGÍA (UNICIT)
    "universidad industrial de santander": 119,  # Universidad Industrial de Santander
    "universidad internacional de ciencia y tecnología": 120,  # Universidad Internacional de Ciencia y Tecnología
    "universidad la gran colombia": 121,  # Universidad La Gran Colombia
    "universidad la salle bajio": 122,  # Universidad La Salle Bajio
    "universidad libre": 123,  # Universidad Libre
    "universidad mayor, real y pontificia de san francisco xavier de chuquisaca": 124,  # Universidad Mayor, Real y Pontificia de San Francisco Xavier de Chuquisaca
    "universidad metropolitana - unimet": 125,  # Universidad Metropolitana - UNIMET
    "universidad militar nueva granada": 126,  # UNIVERSIDAD MILITAR NUEVA GRANADA
    "universidad nacional abierta y a distancia": 127,  # Universidad Nacional Abierta y a Distancia
    "universidad nacional arturo jauretche": 128,  # Universidad Nacional Arturo Jauretche
    "universidad nacional de córdoba": 129,  # Universidad Nacional de Córdoba
    "universidad nacional de cuyo": 130,  # Universidad Nacional de Cuyo
    "universidad nacional de hurlingham": 131,  # Universidad Nacional de Hurlingham
    "universidad nacional de loja": 132,  # UNIVERSIDAD NACIONAL DE LOJA
    "universidad nacional de mar del plata": 133,  # Universidad Nacional de Mar del Plata
    "universidad nacional de río negro": 134,  # Universidad Nacional de Río Negro
    "universidad nacional de san juan": 135,  # Universidad Nacional de San Juan
    "universidad nacional del este": 136,  # Universidad Nacional del Este
    "universidad nacional del litoral": 137,  # Universidad Nacional del Litoral
    "universidad nacional del nordeste": 138,  # Universidad Nacional del Nordeste
    "universidad nacional del noroeste de la provincia de buenos aires": 139,  # Universidad Nacional del Noroeste de la Provincia de Buenos Aires
    "universidad nacional del sur": 140,  # Universidad Nacional del Sur
    "universidad particular de especialidades espíritu santo": 141,  # Universidad Particular de Especialidades Espíritu Santo
    "universidad pedagógica de el salvador \"dr. luis alonso aparicio\"": 142,  # Universidad Pedagógica de El Salvador "Dr. Luis Alonso Aparicio"
    "universidad piloto de colombia": 143,  # Universidad Piloto de Colombia
    "universidad politécnica estatal del carchi": 144,  # Universidad Politécnica Estatal del Carchi
    "universidad politécnica salesiana": 145,  # Universidad Politécnica Salesiana
    "universidad privada abierta latinoamericana": 146,  # Universidad Privada Abierta Latinoamericana
    "universidad privada de santa cruz de la sierra": 147,  # Universidad Privada de Santa Cruz de la Sierra
    "universidad privada del este": 148,  # Universidad Privada del Este
    "universidad privada del norte": 149,  # Universidad Privada del Norte
    "universidad privada del valle": 150,  # Universidad Privada del Valle
    "universidad privada domingo savio": 151,  # Universidad Privada Domingo Savio
    "universidad salvadoreña alberto masferrer": 152,  # Universidad Salvadoreña Alberto Masferrer
    "universidad san gregorio de portoviejo": 153,  # UNIVERSIDAD SAN GREGORIO DE PORTOVIEJO
    "universidad santo tomás, seccional bogotá": 154,  # Universidad Santo Tomás, Seccional Bogotá
    "universidad santo tomás, seccional bucaramanga": 155,  # Universidad Santo Tomás, Seccional Bucaramanga
    "universidad santo tomás, seccional medellín": 156,  # Universidad Santo Tomás, Seccional Medellín
    "universidad santo tomás, seccional tunja": 157,  # Universidad Santo Tomás, Seccional Tunja
    "universidad santo tomás, seccional villavicencio": 158,  # Universidad Santo Tomás, Seccional Villavicencio
    "universidad sek": 159,  # Universidad SEK
    "universidad técnica de babahoyo": 160,  # Universidad Técnica de Babahoyo
    "universidad técnica de machala": 161,  # Universidad Técnica de Machala
    "universidad técnica particular de loja": 162,  # Universidad Técnica Particular de Loja
    "universidad tecnológica de bolívar": 163,  # Universidad Tecnológica de Bolívar
    "universidad tecnológica de panamá": 164,  # Universidad Tecnológica de Panamá
    "universidad tecnológica de pereira": 165,  # Universidad Tecnológica de Pereira
    "universidad tecnológica del perú": 166,  # Universidad Tecnológica del Perú
    "universidad tecnológica privada de santa cruz - utepsa": 167,  # Universidad Tecnológica Privada de Santa Cruz - UTEPSA
    "universidad vasco de quiroga": 168,  # UNIVERSIDAD VASCO DE QUIROGA
    "universidad veracruzana": 169,  # Universidad Veracruzana
    "universidade alto vale do rio do peixe - uniarp": 170,  # Universidade Alto Vale do Rio do Peixe - UNIARP
    "universidade comunitária da região de chapecó": 171,  # Universidade Comunitária da Região de Chapecó
    "universidade da região de joinville - univille": 172,  # Universidade da Região de Joinville - Univille
    "universidade de santa cruz do sul": 173,  # Universidade de Santa Cruz do Sul
    "universidade do estado de santa catarina": 174,  # Universidade do Estado de Santa Catarina
    "universidade do extremo sul catarinense": 175,  # Universidade do Extremo Sul Catarinense
    "universidade do oeste de santa catarina": 176,  # Universidade do Oeste de Santa Catarina
    "universidade do planalto catarinense - uniplac": 177,  # Universidade do Planalto Catarinense - UNIPLAC
    "universidade do vale do itajaí - univali": 178,  # UNIVERSIDADE DO VALE DO ITAJAÍ - UNIVALI
    "universidade federal de pernambuco / ufpe": 179,  # Universidade Federal de Pernambuco / UFPE
    "universidade federal de rondonópolis - ufr": 180,  # Universidade Federal de Rondonópolis - UFR
    "universidade federal de uberlândia": 181,  # Universidade Federal de Uberlândia
    "universidade veiga de almeida": 182,  # Universidade Veiga de Almeida
    "université du québec à trois-rivières": 183,  # Université du Québec à Trois-Rivières
}

_NAME_TO_APP_ID_MAP: dict[str, dict[str, Optional[int]]] = {
    "universities": _NAME_TO_APP_UNIVERSITIES,
}

def emoviesNameToAppIdCatalog(catalog: str, name: Optional[str]) -> Optional[int]:
    if name is None:
        return None

    appId = _NAME_TO_APP_ID_MAP.get(catalog, {}).get(name.strip().lower())
    if appId is None:
        logging.debug(
            "Nombre '%s' no encontrado en catálogo '%s'",
            name,
            catalog,
        )
        return None

    return appId