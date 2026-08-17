# AGENTS.md — ElectivaUCAB News Telegram Bot

Bot de Telegram que monitorea cursos disponibles en [eMOVIES](https://emovies.oui-iohe.org/en/page-our-courses/) y notifica a los usuarios según filtros configurables por chat. Python 3.11+, arquitectura limpia (clean architecture).

## Estructura del proyecto

```
ElectivaUCABNewsTelegramBot/
├── scripts/
│   └── seed.py                    # Creación de tablas y catálogos en PostgreSQL
├── src/                           # Código fuente (arquitectura limpia por capas)
│   ├── port/                      # Capa de entrada: bot de Telegram y tareas
│   │   ├── telegramBot/
│   │   │   ├── main.py            # Punto de entrada: crea TeleBot, registra comandos
│   │   │   └── command/           # Comandos del bot
│   │   │       ├── startCommand.py
│   │   │       ├── helpCommand.py
│   │   │       ├── subscribeCommand.py
│   │   │       ├── unsubscribeCommand.py
│   │   │       └── unknownCommand.py
│   │   └── task/                  # Crons jobs
│   │       ├── syncCoursesTask.py             # Sincroniza cursos desde eMOVIES
│   │       └── sendCoursesToSubcriptorsTask.py # Envía cursos nuevos a suscriptores
│   ├── aplication/                # Casos de uso (orquestan domain + infraestructure)
│   │   ├── syncCoursesUseCase.py
│   │   ├── sendCourseToAllUseCase.py
│   │   ├── subscribeChatUseCase.py
│   │   ├── unsubscribeChatUseCase.py
│   │   ├── getLastUpdateUseCase.py
│   │   ├── getUserCountUseCase.py
│   │   ├── getUserFiltersUseCase.py
│   │   ├── resetFiltersUseCase.py
│   │   └── sendFiltersToUserUseCase.py
│   ├── domain/                    # Capa de dominio: entidades y contratos
│   │   ├── model/
│   │   │   ├── courseModel.py
│   │   │   └── chatConfigModel.py
│   │   └── repository/            # Contratos (interfaces) por capa
│   │       ├── courseRepository.py     # Contrato de origen de cursos (eMOVIES/AUSJAL)
│   │       ├── databaseRepository.py   # Contrato de persistencia (PostgreSQL)
│   │       └── notifierRepository.py   # Contrato de notificación (Telegram)
│   ├── infraestructure/           # Capa de infraestructura: implementaciones
│   │   ├── dbConnection.py        # Conexión PostgreSQL singleton con reintentos
│   │   ├── dto/                   # Data transfer objects (pydantic)
│   │   │   ├── database/          #   chatConfigsDto, courseDto, countriesDto,
│   │   │   │                      #   courseLevelsDto, disciplinaryFieldsDto,
│   │   │   │                      #   languagesDto, universitiesDto
│   │   │   └── emovies/           #   emovieApiParamsDto, emovieApiResponseDto,
│   │   │                          #   emovieswebScraperCourseDto
│   │   ├── mapper/
│   │   │   ├── courseDtoMapper.py        # Traduce IDs de catálogo ↔ nombres
│   │   │   └── emovies/
│   │   │       ├── emovieMapper.py
│   │   │       └── emoviesCatalogTranslator.py
│   │   └── repositoryImp/         # Implementaciones de los contratos
│   │       ├── emoviesCoursesRepositoryImp.py      # Implementa CourseRepository (eMOVIES)
│   │       ├── ausjalCoursesRepositoryImp.py       # Implementa CourseRepository (AUSJAL)
│   │       ├── postgresDatabaseRepositoryImp.py    # Implementa DatabaseRepository
│   │       └── telegramNotifierRepositoryImp.py    # Implementa notifierRepository
│   └── config/
│       └── defaultValuesCatalog.py   # Catálogos por defecto (países, niveles, áreas…)
```

### Reglas de la arquitectura

- `domain/` define contratos (interfaces) sin dependencias externas. Los contratos viven en `domain/repository/`.
- `infraestructure/` implementa esos contratos (HTTP, scraping, PostgreSQL) en `infraestructure/repositoryImp/`.
- `aplication/` contiene los casos de uso que conectan dominio e infraestructura.
- `port/` es la entrada: bot de Telegram (`port/telegramBot/`) y tareas programadas (`port/task/`).
- Los nombres de carpeta están escritos así en el repo (`aplication`, `infraestructure`, `repositoryImp`) — respetarlos al importar.
- La conexión a BD es un singleton con reintentos configurable por env (`dbConnection.py`): `DB_CONNECTION_MAX_RETRIES` y `DB_CONNECTION_RETRY_DELAY_SECONDS`.

## Base de datos (PostgreSQL)

**chatconfigs** — una fila por chat de Telegram (PK = `id`).

| Columna | Tipo | Descripción |
|---|---|---|
| id | BIGINT (Long int) | PK — ID del chat de Telegram |
| lastrevision | DATE | Última fecha de revisión de cursos |
| is_subscribed | BOOLEAN | Indica si el chat recibe notificaciones (default TRUE) |
| uni_countries | INT | FK → `countries(id)` |
| disciplinary_field | INT | FK → `disciplinary_fields(id)` |
| course_university | INT | FK → `universities(id)` |
| uni_languages | INT | FK → `languages(id)` |
| course_levels | INT | FK → `course_levels(id)` |
| key_word | CHAR(50) | Palabra clave de búsqueda |

**Tablas catálogo** — cada una con dos columnas: `id` (SERIAL, PK) y una columna `CHAR(100) NOT NULL UNIQUE` con el valor:

- `universities` — universidades
- `disciplinary_fields` — áreas disciplinarias
- `countries` — países
- `languages` — idiomas
- `course_levels` — niveles académicos

El script `scripts/seed.py` inserta los valores en `countries`, `course_levels` y `disciplinary_fields` desde `src/config/defaultValuesCatalog.py` (`catalogValues(catalog)`). `universities` y `languages` quedan vacíos hasta que se provean datos.

**courses_sources** — catálogo de fuentes de cursos:

| Columna | Tipo | Descripción |
|---|---|---|
| id | SERIAL | PK |
| source | CHAR(100) | Nombre de la fuente (p. ej. `emovies`), UNIQUE |

**courses** — tabla de cursos sincronizados desde la fuente (las columnas de catálogo son FKs a las tablas catálogo):

| Columna | Tipo | Descripción |
|---|---|---|
| id | SERIAL | PK |
| source_id | INT | FK → `courses_sources(id)` |
| external_id | INT | ID del curso en la fuente |
| title | VARCHAR(255) | Título |
| url | TEXT | URL del curso |
| uni_countries | INT | FK → `countries(id)` |
| disciplinary_field | INT | FK → `disciplinary_fields(id)` |
| course_university | INT | FK → `universities(id)` |
| uni_languages | INT | FK → `languages(id)` |
| course_levels | INT | FK → `course_levels(id)` |
| start_class_date | DATE | Inicio de clases |
| end_class_date | DATE | Fin de clases |
| start_inscription_date | DATE | Inicio de inscripción |
| end_inscription_date | DATE | Fin de inscripción |
| description | TEXT | Descripción |
| study_hours | INT | Horas de estudio |
| slots | INT | Cupos |
| modified_date | DATE | Última fecha de modificación (para detectar cursos nuevos) |

**Mapeo de catálogos eMOVIES ↔ BD**: los códigos de catálogo de eMOVIES se traducen a IDs de catálogo de la app mediante las equivalencias directas código→ID almacenadas en `EmoviesCatalogTranslator` (en `src/infraestructure/mapper/emovies/emoviesCatalogTranslator.py`), sin nombres intermedios ni consultas a la BD. En la dirección inversa, `courseDtoMapper` traduce los IDs de catálogo de vuelta a nombres cargando mapas ID→nombre consultando la BD (método `_catalogNameMaps` de `PostgresDatabaseRepositoryImp`).

## Dependencias (requirements.txt)

| Paquete | Versión | Propósito |
|---|---|---|
| pyTelegramBotAPI | 4.32.0 | Cliente de la Telegram Bot API. Clase `TeleBot`, decorador `@bot.message_handler`, respuestas con `bot.reply_to`/`bot.send_message`. Import: `from telebot import TeleBot` |
| beautifulsoup4 | 4.15.0 | Scraping HTML/XML: clase `BeautifulSoup`, búsqueda con `find()`/`find_all()`, selectores CSS con `soup.select()`. Requiere un parser (p. ej. `html.parser` de la stdlib) |
| requests | 2.33.0 | Cliente HTTP para consumir la API de eMOVIES |
| psycopg | 3.3.3 | Driver de PostgreSQL v3 (`psycopg.connect`) para persistencia |
| psycopg-binary | 3.3.3 | Binarios compilados de psycopg (instalación sin compilación) |
| python-dotenv | 1.2.2 | Carga variables de entorno desde `.env` (`load_dotenv()`, `get_key()`) |
| pydantic | 2.13.4 | Modelado y validación de DTOs: clases `BaseModel`, parseo/validación de datos y serialización. Import: `from pydantic import BaseModel` |
| annotated-types | 0.8.0 | Soporte de tipos anotados (`Annotated`) usado por pydantic |
| certifi | 2026.2.25 | Bundle de certificados CA de Mozilla para verificación SSL (usado por requests) |
| charset-normalizer | 3.4.6 | Detección y normalización de codificaciones (dependencia de requests) |
| idna | 3.11 | Soporte de nombres de dominio internacionalizados (dependencia de requests) |
| pydantic_core | 2.46.4 | Núcleo compilado (Rust) de pydantic v2: validación de alto rendimiento (dependencia de pydantic) |
| soupsieve | 2.9.2 | Motor de selectores CSS usado internamente por beautifulsoup4 |
| typing-inspection | 0.4.4 | Inspección de tipos en runtime (dependencia de pydantic) |
| urllib3 | 2.6.3 | Cliente HTTP de bajo nivel usado por requests |
| typing_extensions | 4.16.0 | Backports de tipado para versiones antiguas de Python |
| tzdata | 2025.3 | Base de datos IANA de zonas horarias (requerida en Windows) |

### Documentación oficial

- [pyTelegramBotAPI (pytba)](https://pytba.readthedocs.io/) — referencia de `TeleBot`, tipos (`telebot.types`) y formato de mensajes
- [Beautiful Soup 4](https://beautiful-soup-4.readthedocs.io/) — navegación y búsqueda en el árbol de parseo
- [psycopg 3](https://www.psycopg.org/psycopg3/docs/) — conexión y operaciones con PostgreSQL
- [Requests](https://requests.readthedocs.io/) — cliente HTTP
- [python-dotenv](https://pypi.org/project/python-dotenv/) — variables de entorno.
- [Pydantic](https://pydantic.dev/) — documentación de modelos `BaseModel`, validación y serialización