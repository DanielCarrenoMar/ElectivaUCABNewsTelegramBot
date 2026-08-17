import logging

from src.aplication.unsubscribeChatUseCase import UnsubscribeChatUseCase
from infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


def register(bot):
    unsubscribeChatUseCase = UnsubscribeChatUseCase(PostgresDatabaseRepositoryImp())

    @bot.message_handler(commands=["desuscribirse"])
    def handle_unsubscribe(message):
        try:
            unsubscribeChatUseCase.execute(message.chat.id)
            bot.reply_to(
                message,
                "⏸️ Te has desuscrito de las notificaciones. Usa /suscribirse para volver.",
            )
        except Exception:
            logging.exception("unsubscribeCommand: error al desuscribir el chat %s", message.chat.id)
            bot.reply_to(message, "❌ Ocurrió un error al desuscribirte. Inténtalo más tarde.")