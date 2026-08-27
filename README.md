<a>
    <img src="https://github.com/DanielCarrenoMar/Snake-XPR_UCAB/assets/144462396/d30c8055-4d82-4a05-b0f3-5f74c85ffb7f" alt="Logo" title="Logo" align="right" height="70" />
</a>

# 	![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff) EMovies News. Bot Telegram

[![status: active](https://github.com/GIScience/badges/raw/master/status/active.svg)](https://github.com/GIScience/badges#active)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?logo=telegram&logoColor=white)

Bot de Telegram para monitorear cursos disponibles para internacionalización en los programas [eMOVIES](https://emovies.oui-iohe.org/en/page-our-courses/) y [Ausjal](https://intercampusausjal.com/asignaturas-virtuales/) notificando cuando aparece uno nuevo según filtros configurables por el usuario.

> 👀 [Prueba el bot](https://t.me/materiasInterNoticiasBot)

## Características ⭐
- Guardado de configuración de filtro para cada usuario.
- Notificación cada 48 horas de nuevos cursos según los filtros del usuario.
- Obtención de cursos centralizada desde diferentes fuentes de información.

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
- Playwright
- PostgreSQL

## Variables de entorno

- `TELEGRAM_BOT_TOKEN`
- `DB_URL`
- `DB_CONNECTION_RETRY_DELAY_SECONDS`
- `DB_CONNECTION_MAX_RETRIES`
- `EMOVIES_PAGE_RETRIES` reintentos por página de la API de eMOVIES.

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

Para ejecutar el bot y las tareas generales:

```bash
pip install -r requirements.txt
```

Para ejecutar la sincronización de cursos desde las fuentes de datos:

```bash
pip install -r requirements-scraper.txt
playwright install --with-deps chromium
```

> El archivo correcto es `requirements-scraper.txt`. Este incluye las dependencias de `requirements.txt` y agrega Playwright.

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
DB_URL=postgresql://usuario:contraseña@host:5432/nombre_base_de_datos
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

## 6. Crear las tablas y catálogos

Con el entorno virtual activo, ejecuta:

```bash
python -m scripts.seed
```

Este comando crea las tablas necesarias, índices, catálogos y fuentes de cursos en PostgreSQL.

## 7. Sincronizar las fuentes de datos con la base de datos

Para consultar e insertar los cursos de eMOVIES y AUSJAL en la base de datos:

```bash
python -m src.port.task.syncCoursesTask
```

La variable `DB_URL` debe estar configurada correctamente antes de ejecutar este comando.

## 8. Ejecutar el bot de Telegram

En otra terminal, activa nuevamente el entorno virtual y ejecuta:

```bash
python -m src.port.telegramBot.main
```

El bot comenzará a escuchar mensajes de Telegram.

## 9. Enviar cursos nuevos a los suscriptores

Para ejecutar manualmente la tarea de notificaciones:

```bash
python -m src.port.task.sendCoursesToSubcriptorsTask
```

## 10. Desactivar el entorno virtual

Cuando termines, ejecuta:

```bash
deactivate
```
