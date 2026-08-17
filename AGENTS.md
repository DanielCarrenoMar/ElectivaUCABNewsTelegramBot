# AGENTS.md — ElectivaUCAB News Telegram Bot

Bot de Telegram que monitorea cursos disponibles en [eMOVIES](https://emovies.oui-iohe.org/en/page-our-courses/) y notifica a los usuarios según filtros configurables por chat. Python 3.11+, arquitectura limpia (clean architecture).

## Estructura del proyecto

```
ElectivaUCABNewsTelegramBot/
├── src/                          # Código fuente (arquitectura limpia por capas)
│   ├── app/                      # Capa de aplicación: entrada y orquestación
│   │   ├── telegramBot/
│   │   │   ├── main.py           # Punto de entrada: crea TeleBot, registra comandos
│   │   │   └── command/          # Comandos del bot
│   │   └── task/                 # Crons jobs
│   ├── aplication/               # Casos de uso (orquestan domain + infraestructure)
│   ├── domain/                   # Capa de dominio: entidades y contratos
│   │   ├── model/
│   └── infraestructure/          # Capa de infraestructura: implementaciones
│       ├── dto/
│       ├── mapper/
```

### Reglas de la arquitectura

- `domain/` define contratos (interfaces) sin dependencias externas.
- `infraestructure/` implementa esos contratos (HTTP, scraping, PostgreSQL).
- `aplication/` contiene los casos de uso que conectan dominio e infraestructura.
- `app/` es la entrada: bot de Telegram y tareas programadas.
- Los nombres de carpeta están escritos así en el repo (`aplication`, `infraestructure`) — respetarlos al importar.

## Base de datos (PostgreSQL)

**ChatConfigs** — una fila por chat de Telegram (PK = `id`).

| Columna | Tipo | Descripción |
|---|---|---|
| id | BIGINT (Long int) | PK — ID del chat de Telegram |
| lastrevision | DATE | Última fecha de revisión de cursos |
| uni_countries | INT | FK → `Countries(id)` |
| disciplinary_field | INT | FK → `Disciplinary_fields(id)` |
| course_university | INT | FK → `Universities(id)` |
| uni_languages | INT | FK → `Languages(id)` |
| course_levels | INT | FK → `Course_levels(id)` |
| key_word | CHAR(50) | Palabra clave de búsqueda |

**Tablas catálogo** — cada una con dos columnas: `id` (INT/BIGINT, PK) y una columna `CHAR` con el valor:

- `Universities` — universidades
- `Disciplinary_fields` — áreas disciplinarias
- `Countries` — países
- `Languages` — idiomas
- `Course_levels` — niveles académicos

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
