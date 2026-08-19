
from src.aplication.subscribeChatUseCase import SubscribeChatUseCase


def register(bot):
    @bot.message_handler(commands=["start"])
    def handle_start(message):
        bot.reply_to(
            message,
            "👋 ¡Bienvenido! Este bot te enviará notificaciones de nuevos cursos según tus filtros personalizados. Puedes usar /filtros para cambiarlos, /desuscribirse para dejar de recibir avisos y /ayuda para ver todos los comandos disponibles.",
        )

        SubscribeChatUseCase().execute(message.chat.id)
       
