import os

from telebot import TeleBot
from dotenv import load_dotenv, get_key
import logging
from src.app.telegramBot.command import startCommand, helpCommand, unknownCommand, subscribeCommand, unsubscribeCommand

def main():
    logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )
    
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Falta variable de entorno TELEGRAM_BOT_TOKEN")

    bot = TeleBot(token, parse_mode="HTML")

    startCommand.register(bot)
    helpCommand.register(bot)
    subscribeCommand.register(bot)
    unsubscribeCommand.register(bot)
    unknownCommand.register(bot)

if __name__ == "__main__":
    main()