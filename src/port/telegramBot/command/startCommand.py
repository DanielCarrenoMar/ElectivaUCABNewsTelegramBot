
from src.aplication.subscribeChatUseCase import SubscribeChatUseCase


def register(bot):
    @bot.message_handler(commands=["start"])
    def handle_start(message):
        bot.reply_to(
            message,
            "👋 Hola. Usa /suscribirse para activar las notificaciones, /desuscribirse para pausarlas o /ayuda para ver todos los comandos.",
        )

        SubscribeChatUseCase().execute(message.chat.id)
       
