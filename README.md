<a>
    <img src="https://github.com/DanielCarrenoMar/Snake-XPR_UCAB/assets/144462396/d30c8055-4d82-4a05-b0f3-5f74c85ffb7f" alt="Logo" title="Logo" align="right" height="70" />
</a>

# 	![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff) EMovies News. Bot Telegram

[![status: active](https://github.com/GIScience/badges/raw/master/status/active.svg)](https://github.com/GIScience/badges#active)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?logo=telegram&logoColor=white)

Bot de Telegram para monitorear cursos disponibles en [eMOVIES](https://emovies.oui-iohe.org/en/page-our-courses/) y notificar cuando aparece uno nuevo según filtros configurables por chat.

> 👀 [Prueba el bot](https://t.me/emovies_news_bot)

## Características ⭐
- Guardado de configuración de filtro para cada usuario.
- Notificación cada 24 horas de nuevos cursos según los filtros del usuario.

## Comandos del bot

- `/start` inicia el bot en el chat.
- `/help` muestra ayuda.
- `/filters` permite ver y modificar los filtros activos.
- `/resetfilters` vuelve a filtros por defecto.
- `/check` consulta inmediatamente y notifica cursos nuevos.
- `/on` activa monitoreo automático del chat.
- `/off` pausa monitoreo automático del chat.

# Para desarrolladores

## Requisitos

- Python 3.11+
- Dependencias de `requirements.txt`
- Token de bot de Telegram

## Variables de entorno

- `TELEGRAM_BOT_TOKEN` (obligatoria)
- `POLL_INTERVAL_SECONDS` (opcional, por defecto `2700`)
- `DB_URL` (obligatoria para persistencia)

## Ejecutar localmente

1. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

2. Colocar variables de entorno.
3. Inciar entorno venv
4. Ejecutar:

   Seed de database
   ```bash
   .venv\Scripts\python.exe -m scripts.seed
   ```

   Tarea sincronizar db con fuentes de datos
   ```bash
   .venv\Scripts\python.exe -m src.port.task.syncCoursesTask    
   ```
