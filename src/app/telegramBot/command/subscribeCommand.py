import logging

from src.aplication.subscribeChatUseCase import SubscribeChatUseCase
from infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


def register(bot):
    subscribeChatUseCase = SubscribeChatUseCase(PostgresDatabaseRepositoryImp())

    @bot.message_handler(commands=["suscribirse"])
    def handle_subscribe(message):
        try:
            subscribeChatUseCase.execute(message.chat.id)
            bot.reply_to(message, "✅ Te has suscrito a las notificaciones.")
        except Exception:
            logging.exception("subscribeCommand: error al suscribir el chat %s", message.chat.id)
            bot.reply_to(message, "❌ Ocurrió un error al suscribirte. Inténtalo más tarde.")