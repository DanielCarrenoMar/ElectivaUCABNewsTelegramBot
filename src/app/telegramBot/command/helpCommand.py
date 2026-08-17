def register(bot):
    @bot.message_handler(commands=["help"])
    def handle_help(message):
        bot.reply_to(
            message,
            (
                "<b>Comandos</b>\n"
                "/start - iniciar bot en este chat\n"
                "/help - mostrar esta ayuda\n"
                "/suscribirse - activar notificaciones de cursos\n"
                "/desuscribirse - pausar notificaciones de cursos"
            ),
        )
