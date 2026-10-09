<a>
    <img src="https://github.com/DanielCarrenoMar/Snake-XPR_UCAB/assets/144462396/d30c8055-4d82-4a05-b0f3-5f74c85ffb7f" alt="Logo" title="Logo" align="right" height="70" />
</a>

# 	![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff) EMovies News. Bot Telegram

[![status: active](https://github.com/GIScience/badges/raw/master/status/active.svg)](https://github.com/GIScience/badges#active)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?logo=telegram&logoColor=white)

Bot de Telegram que notifica los cursos de internacionalización que publica el catálogo
[Electiva Internacional](https://emovies.oui-iohe.org/en/page-our-courses/), según los filtros
configurados por cada chat.

El bot **no recopila ni almacena los cursos**: el catálogo es propiedad de otro sistema y el bot
solo lo lee. Cada base de datos externa publica sus propios cursos; cuando uno se publica o se
actualiza, los chats suscritos que coinciden con sus filtros lo reciben.

> 👀 [Prueba el bot](https://t.me/materiasInterNoticiasBot)

## Características ⭐
- Guardado de configuración de filtro para cada usuario.
- Notificación cada 48 horas de cursos nuevos o actualizados según los filtros del usuario.
- Catálogos (países, idiomas, niveles, áreas) leídos del catálogo, sin catálogos duplicados.

## Comandos del bot

- `/start` inicia el Bot y te subscribe a las notificaciones de cursos.
- `/ayuda` muestra todos los comandos.
- `/filtros` permite ver y modificar los filtros activos.
- `/suscribirse` te subscribe a las notificaciones de cursos.
- `/desuscribirse` te desubscribe a las notificaciones de cursos.

# Para desarrolladores

## Tecnologías

- Python 3.11+
- Api de Telegram
- PostgreSQL (dos conexiones: una propia y una de solo lectura al catálogo)

## Bases de datos

El bot habla con dos bases distintas:

| Variable | Contenido | Acceso |
|---|---|---|
| `DB_URL` | Suscripciones y filtros de cada chat (`chatconfigs`). Única tabla propia. | lectura y escritura |
| `COURSES_DB_URL` | Catálogo de cursos y sus catálogos, propiedad de otro sistema. | **solo lectura** |

Los filtros de `chatconfigs` guardan la clave natural del catálogo (`countries.iso_code`,
`languages.code`, `academic_levels.id`, `knowledge_areas.name`), no un id propio: no hay llave
foránea posible entre bases distintas.

## Variables de entorno

- `TELEGRAM_BOT_TOKEN`
- `DB_URL` — suscripciones y filtros de chat
- `COURSES_DB_URL` — catálogo de cursos (solo lectura)
- `DB_CONNECTION_RETRY_DELAY_SECONDS`
- `DB_CONNECTION_MAX_RETRIES`

## Instrucciones para iniciar en local 

## 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd ElectivaUCABNewsTelegramBot
```

## 2. Crear y activar el entorno virtual

### Windows — PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación, ejecuta:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Después, activa nuevamente el entorno virtual.

### Windows — CMD

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Ubuntu o Debian, si el comando anterior falla, instala el módulo de entornos virtuales:

```bash
sudo apt update
sudo apt install python3-venv
```

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Instalar las dependencias

Con el entorno virtual activo, actualiza `pip`:

```bash
python -m pip install --upgrade pip
```

Para ejecutar el bot y las tareas programadas:

```bash
pip install -r requirements.txt
```

## 4. Configurar las variables de entorno

Copia el archivo de ejemplo.

### Linux y macOS

```bash
cp .env.example .env
```

### Windows — PowerShell

```powershell
Copy-Item .env.example .env
```

Edita `.env` y completa al menos las siguientes variables:

```env
TELEGRAM_BOT_TOKEN=TU_TOKEN_AQUI
DB_URL=postgresql://usuario:contraseña@host:5432/base_de_suscripciones
COURSES_DB_URL=postgresql://usuario:contraseña@host:5432/base_del_catalogo
```

No compartas ni subas el archivo `.env` al repositorio.

## 5. Obtener el token del bot con BotFather

1. Abre Telegram y busca el usuario oficial `@BotFather`.
2. Inicia una conversación y ejecuta `/start`.
3. Ejecuta el comando `/newbot`.
4. Escribe el nombre visible del bot.
5. Escribe un nombre de usuario único que termine en `bot`.
6. BotFather responderá con el token del bot.
7. Copia el token y asígnalo a `TELEGRAM_BOT_TOKEN` en el archivo `.env`.

Ejemplo:

```env
TELEGRAM_BOT_TOKEN=123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

No publiques este token. Si se filtra, revócalo desde BotFather usando `/revoke` y genera uno nuevo.

## 6. Crear la tabla de suscripciones

Con el entorno virtual activo, ejecuta:

```bash
python -m scripts.seed
```

Esto crea la única tabla propia del bot, `chatconfigs`. Los cursos y sus catálogos viven en la base
del catálogo y el bot nunca los escribe.

Si vienes de una versión anterior del bot, migra los filtros existentes a las claves naturales del
catálogo con:

```bash
python -m scripts.migrate_chatconfigs_filters
```

El script es idempotente y reporta valor por valor cualquier filtro que no se pueda resolver. Un
filtro no resoluble queda en `NULL`, es decir "cualquiera", así que ese chat recibirá más
notificaciones, nunca menos.

## 7. Ejecutar el bot de Telegram

En otra terminal, activa nuevamente el entorno virtual y ejecuta:

```bash
python -m src.port.telegramBot.main
```

El bot comenzará a escuchar mensajes de Telegram.

## 8. Enviar cursos nuevos a los suscriptores

Para ejecutar manualmente la tarea de notificaciones:

```bash
python -m src.port.task.sendCoursesToSubcriptorsTask
```

La tarea envía a cada chat suscrito los cursos cuyo `updated_at` es posterior a la marca de agua
del chat (`chatconfigs.lastrevision`), y luego adelanta esa marca. La fecha de publicación no la
calcula el bot: es la que publica el catálogo.

## 9. Desactivar el entorno virtual

Cuando termines, ejecuta:

```bash
deactivate
```
