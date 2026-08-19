import logging
import os
import pathlib
import sys

from dotenv import load_dotenv
from telebot import TeleBot

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s.%(funcName)s: %(message)s",
    force=True,
)

CHANGELOG_MESSAGE = (
    "<b>\U0001F4E2 \u00A1Actualizaci\u00F3n</b>\n"
    "\n"
    "Nueva versi\u00F3n del bot, gracias por usarlo!\n"
    "\n"
    "<b>\U0001F50E M\u00E1s informaci\u00F3n de los cursos</b>\n"
    "Ahora cada curso muestra informaci\u00F3n m\u00E1s completa: fechas de inicio y fin "
    "de clases, fechas de inscripci\u00F3n, descripci\u00F3n, horas de estudio, cupos "
    "disponibles y m\u00E1s detalles.\n"
    "\n"
"<b>\U0001F30D Notificaciones de cursos AUSJAL</b>\n"
    "A partir de ahora tambi\u00E9n se notificar\u00E1n los cursos publicados en "
    "<a href=\"https://intercampusausjal.com/asignaturas-virtuales/\">AUSJAL</a>, "
    "adem\u00E1s de los de eMOVIES.\n"
)


def sendChangelogToUsers():
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Falta variable de entorno TELEGRAM_BOT_TOKEN")
    if not os.getenv("DB_URL"):
        raise RuntimeError("Falta variable de entorno DB_URL")

    bot = TeleBot(token, parse_mode="HTML")
    databaseRepository = PostgresDatabaseRepositoryImp()
    chatConfigs = databaseRepository.getSubcriptorsChatConfig()

    totalSent = 0
    for chat in chatConfigs:
        try:
            bot.send_message(
                chat.id,
                CHANGELOG_MESSAGE,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            totalSent += 1
        except Exception:
            logging.exception("sendChangelogToUsers: error enviando el mensaje al chat %s", chat.id)

    logging.info(
        "sendChangelogToUsers: mensaje enviado a %d de %d chats suscritos",
        totalSent,
        len(chatConfigs),
    )


if __name__ == "__main__":
    sendChangelogToUsers()