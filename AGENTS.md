# AGENTS.md — ElectivaUCAB News Telegram Bot

Bot de Telegram que notifica los cursos de internacionalización publicados en un catálogo externo
y notifica a los usuarios según filtros configurables por chat. Python 3.11+, arquitectura limpia
(clean architecture).

> **El bot no es dueño de los cursos.** El catálogo y sus catálogos pertenecen a otro sistema y el
> bot solo los lee. La base propia conserva una única tabla: `chatconfigs`.

## Estructura del proyecto

```
ElectivaUCABNewsTelegramBot/
├── scripts/
│   ├── seed.py                        # Crea chatconfigs (única tabla propia)
│   └── migrate_chatconfigs_filters.py # Convierte filtros INT a claves naturales (idempotente)
├── src/                               # Código fuente (arquitectura limpia por capas)
│   ├── port/                          # Capa de entrada: bot de Telegram y tareas
│   │   ├── telegramBot/
│   │   │   ├── main.py                # Punto de entrada: crea TeleBot, registra comandos
│   │   │   └── command/               # Comandos del bot
│   │   │       ├── startCommand.py
│   │   │       ├── helpCommand.py
│   │   │       ├── subscribeCommand.py
│   │   │       ├── unsubscribeCommand.py
│   │   │       ├── filtersCommand.py  # Teclado de filtros, lee catálogos del catálogo externo
│   │   │       └── unknownCommand.py
│   │   └── task/                      # Tareas programadas
│   │       ├── task.py                # Decorador log_task_duration
│   │       └── sendCoursesToSubcriptorsTask.py # Envía cursos nuevos a los suscriptores
│   ├── aplication/                    # Casos de uso (orquestan domain + infraestructure)
│   │   ├── subscribeChatUseCase.py
│   │   ├── unsubscribeChatUseCase.py
│   │   ├── getUserFiltersUseCase.py
│   │   ├── updateUserFilterUseCase.py
│   │   └── sendCourseToSubcriptorsUseCase.py # Emparejamiento de filtros en Python + marca de agua
│   ├── domain/                        # Capa de dominio: entidades y contratos
│   │   ├── model/
│   │   │   ├── courseModel.py         # CourseRecordDto, CatalogEntry, ShowCourseModel
│   │   │   └── chatConfigModel.py     # ChatConfig (filtros = claves naturales)
│   │   └── repository/                # Contratos (interfaces) por capa
│   │       ├── coursesRepository.py   # Contrato de solo lectura del catálogo
│   │       ├── databaseRepository.py   # Contrato de la base propia (chatconfigs)
│   │       └── notifierRepository.py   # Contrato de notificación (Telegram)
│   ├── infraestructure/               # Capa de infraestructura: implementaciones
│   │   ├── dbConnection.py            # Dos conexiones: get_db_connection / get_courses_db_connection
│   │   ├── dto/                       # Data transfer objects (pydantic)
│   │   │   └── database/              #   chatConfigsDto
│   │   ├── mapper/                    # Traductores entre filas, DTOs y modelos
│   │   │   ├── courseRecordMapper.py  # Fila del catálogo -> CourseRecordDto -> ShowCourseModel
│   │   │   └── chatConfigMapper.py    # ChatConfig <-> ChatConfigsDto
│   │   └── repositoryImp/             # Implementaciones de los contratos
│   │       ├── coursesRepositoryImp.py         # Lectura del catálogo (nunca escribe)
│   │       ├── postgresDatabaseRepositoryImp.py # chatconfigs
│   │       └── telegramNotifierRepositoryImp.py # Telegram
│   └── config/
│       └── __init__.py                # Los catálogos viven en la base externa, no aquí
```

### Reglas de la arquitectura

- `domain/` define contratos (interfaces) sin dependencias externas. Los contratos viven en `domain/repository/`.
- `infraestructure/` implementa esos contratos en `infraestructure/repositoryImp/`.
- `aplication/` contiene los casos de uso que conectan dominio e infraestructura.
- `port/` es la entrada: bot de Telegram (`port/telegramBot/`) y tareas programadas (`port/task/`).
- **Nunca se escribe en la base del catálogo.** `get_courses_db_connection()` es de solo lectura por
  contrato; `CoursesRepositoryImp` solo emite SELECT.
- Los nombres de carpeta están escritos así en el repo (`aplication`, `infraestructure`,
  `repositoryImp`) — respetarlos al importar.
- La conexión a BD son singletons con reintentos configurables por env (`dbConnection.py`):
  `DB_CONNECTION_MAX_RETRIES` y `DB_CONNECTION_RETRY_DELAY_SECONDS`. Importar el módulo **no**
  abre conexión: cada factoría valida su variable al invocarse.

## Las dos bases de datos

| Variable | Base | Contenido | Acceso |
|---|---|---|---|
| `DB_URL` | propia | `chatconfigs` (suscripciones y filtros) | lectura y escritura |
| `COURSES_DB_URL` | externa | catálogo de cursos y sus catálogos | **solo lectura** |

Ambas conexiones comparten la misma política de reintentos y una caché de conexiones indexada por
variable de entorno.

## Base de datos externa: esquema del catálogo

El catálogo es propiedad de otro sistema. El bot lo lee, no lo crea ni lo modifica.

- **`courses`** — `id VARCHAR(32)`, `title`, `description`, `campus_id`, `language_code`,
  `academic_level_id`, `source_id`, `modality`, `credits`, `site_url`, `enrollment_start/end`,
  `course_start/end`, `total_seats`, `available_seats`, `is_active`, `created_at`, **`updated_at`**.
- **`campuses`** → `universities`, y opcionalmente `cities` → `countries`.
- **`course_knowledge_areas`** — relación N:M cursos ↔ áreas (áreas de conocimiento).
- **Catálogos**: `countries` (`iso_code`), `languages` (`code`), `academic_levels` (`id` es texto),
  `knowledge_areas`, `sources`.
- Otras tablas del esquema que el bot **no** consulta: `agreements`, `course_files`.

### Puntos que condicionan el comportamiento

- **La única señal de novedad es `courses.updated_at`.** La marca de agua de cada chat se compara
  contra ella.
- **`updated_at` es `timestamp WITHOUT time zone`; `chatconfigs.lastrevision` es `TIMESTAMPTZ`.**
  Hay que normalizar a UTC antes de comparar (`_asUtc` en `sendCourseToSubcriptorsUseCase.py`), o
  la comparación lanza `TypeError`. Ambas bases están en GMT.
- **El país solo se alcanza por `campus → city → country`, y 2117 de 4167 cursos tienen
  `campus.city_id IS NULL`**, es decir no llegan a ningún país. Por eso ciudad y país van con
  `LEFT JOIN`: un curso sin país **no puede satisfacer un filtro de país** (`None != "CO"`), pero sí
  debe seguir llegando a los chats sin ese filtro.
- No hay índice sobre `updated_at` ni índice trigram para el filtro por palabra clave en la base
  externa. Es responsabilidad del sistema dueño.

## Base de datos propia: chatconfigs

Única tabla que conserva el bot.

| Columna | Tipo | Descripción |
|---|---|---|
| id | BIGINT | PK — ID del chat de Telegram |
| lastrevision | TIMESTAMPTZ (default `now()`) | Marca de agua; se compara contra `courses.updated_at` |
| is_subscribed | BOOLEAN | El chat recibe notificaciones (default TRUE) |
| country_iso_code | VARCHAR(2) | `countries.iso_code` |
| course_university | VARCHAR(150) | `universities.name` |
| course_language_code | VARCHAR(5) | `languages.code` |
| course_level_id | VARCHAR(50) | `academic_levels.id` (texto) |
| disciplinary_field | VARCHAR(100) | `knowledge_areas.name` |
| key_word | VARCHAR(50) | Búsqueda por substring en título o descripción |

**Por qué los filtros son texto y no INT:** los catálogos viejo y nuevo tienen espacios de
identificadores sin relación y no hay llave foránea posible entre bases distintas. Por eso cada
columna guarda la clave natural del catálogo, que es además lo que el emparejamiento compara.

**`lastrevision` es TIMESTAMPTZ y no DATE** porque `updated_at` es un timestamp.

## Notificación: cómo se decide qué se envía

`sendCourseToSubcriptorsUseCase` reemplaza al antiguo `CROSS JOIN chatconfigs × courses`:

1. Lee los chats suscritos. Un chat con `lastrevision IS NULL` se omite (no tiene nada pendiente)
   y no interviene en el mínimo de la consulta.
2. Calcula `min(lastrevision)` y trae **una sola vez** los candidatos con `updated_at` mayor, más
   sus áreas de conocimiento en una segunda consulta por lotes.
3. Por cada chat, `courseMatchesChat` decide en Python: frescura + filtros. Es una función pura, sin
   efectos, ejercitable con fixtures sin base de datos.
4. Envía y adelanta la marca de agua.

**La marca de agua sube al máximo de `updated_at` de TODOS los candidatos, no solo de los que
coincidieron.** Antes avanzaba únicamente con el curso coincidente más nuevo, así que un chat cuyos
filtros no coincidían con nada nunca avanzaba y volvía a recorrer todo su historial en cada corrida.

`nextWatermark` nunca retrocede: si el máximo de candidatos es anterior a la marca actual, se
conserva la actual.

## Migración de datos

`scripts/migrate_chatconfigs_filters.py` convierte los filtros de INT a claves naturales resolviendo
cada valor contra el catálogo por nombre normalizado (NFKD, sin diacríticos, minúsculas, espacios
colapsados). Los catálogos viejos se leen de la base propia; el mapeo de niveles es semántico
(`1→doctorate`, `2→continuing_education`, `3→postgraduate`, `4→undergraduate`,
`5→technical_technological`) porque ambos catálogos nombran distinto.

Es **idempotente**: detecta si las columnas siguen siendo `integer` (no si sus nombres coinciden,
porque `course_university` y `disciplinary_field` mantienen el nombre en ambos esquemas).

Un valor que no resuelve queda en `NULL` y se reporta. El efecto aceptado es que ese filtro se abre
a "cualquiera": el chat recibe más notificaciones, nunca menos.

## Dependencias (requirements.txt)

| Paquete | Versión | Propósito |
|---|---|---|
| pyTelegramBotAPI | 4.32.0 | Cliente de la Telegram Bot API |
| beautifulsoup4 | 4.15.0 | Parseo HTML/XML |
| requests | 2.33.0 | Cliente HTTP |
| psycopg / psycopg-binary | 3.3.3 | Driver de PostgreSQL v3 |
| python-dotenv | 1.2.2 | Variables de entorno desde `.env` |
| pydantic | 2.13.4 | Modelado y validación |
| annotated-types | 0.8.0 | Tipos anotados para pydantic |
| certifi | 2026.2.25 | Bundle de CA de Mozilla (requests) |
| charset-normalizer | 3.4.6 | Detección de codificaciones (requests) |
| idna | 3.11 | Nombres de dominio internacionales (requests) |
| pydantic_core | 2.46.4 | Núcleo compilado de pydantic v2 |
| soupsieve | 2.9.2 | Selectores CSS de beautifulsoup4 |
| typing-inspection | 0.4.4 | Inspección de tipos (pydantic) |
| urllib3 | 2.6.3 | Cliente HTTP de bajo nivel (requests) |
| typing_extensions | 4.16.0 | Backports de tipado |
| tzdata | 2025.3 | Zonas horarias IANA (requerida en Windows) |

Ya no hay `playwright` ni `requirements-scraper.txt`: el bot no scrapea nada.

## Automatización

`.github/workflows/send-courses-to-subscribers.yml` corre cada 2 días a las 13:00 UTC y recibe tres
secrets: `DB_URL`, `COURSES_DB_URL` y `TELEGRAM_BOT_TOKEN`.

## Gotchas conocidos

- **Telegram limita `callback_data` a 64 bytes.** Los valores de filtro son nombres, y tres áreas de
  conocimiento lo superaban (hasta 70 B). `filtersCommand` pone el **índice** del catálogo en el
  botón y resuelve el valor al pulsarlo; ninguna etiqueta se trunca. Al agregar un filtro nuevo,
 verifica que el callback quepa en 64 bytes.
- **Un filtro guardado que ya no está en el catálogo** se muestra como `⚠️ No disponible (valor)`,
  no como "Cualquiera". Un filtro que se ensancha solo en silencio es peor que uno que el usuario
  sabe viejo.
- **El texto de un filtro nunca se pasa por `int()`.** `UpdateUserFilterUseCase` guarda la cadena
  tal cual y convierte vacío o espacios en `NULL`.
- **`updateChatConfig` construye el UPDATE con un dict columna→valor explícito**, no con
  `model_dump()`: los nombres de campo del DTO (`last_revision`) no coinciden con los de columna
  (`lastrevision`) y el `KeyError` quedaba tapado por un `except Exception` del caso de uso.

## Documentación oficial

- [pyTelegramBotAPI (pytba)](https://pytba.readthedocs.io/)
- [Beautiful Soup 4](https://beautiful-soup-4.readthedocs.io/)
- [psycopg 3](https://www.psycopg.org/psycopg3/docs/)
- [Requests](https://requests.readthedocs.io/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [Pydantic](https://pydantic.dev/)