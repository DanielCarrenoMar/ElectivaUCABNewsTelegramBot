def register(bot):
    @bot.message_handler(commands=["help"])
    def handle_help(message):
        bot.reply_to(
            message,
            (
                "<b>Comandos</b>\n"
                "/start - iniciar bot en este chat\n"
                "/filters - ver y editar filtros actuales\n"
                "/resetfilters - restaurar filtros por defecto\n"
                "/check - revisar ahora si hay cursos nuevos\n"
                "/on - activar monitoreo automático\n"
                "/off - pausar monitoreo automático"
            ),
        )
