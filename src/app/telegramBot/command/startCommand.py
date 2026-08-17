
def register(bot):
    @bot.message_handler(commands=["start"])
    def handle_start(message):
        bot.reply_to(
            message,
            "👋 Hola. Usa /filters para configurar filtros o /help para ver todos los comandos.",
        )
       
