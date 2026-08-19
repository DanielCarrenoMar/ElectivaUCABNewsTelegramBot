def register(bot):
    @bot.message_handler(commands=["ayuda"])
    def handle_help(message):
        bot.reply_to(
            message,
            (
                "<b>Comandos</b>\n"
                "/start - iniciar bot en este chat\n"
                "/ayuda - mostrar esta ayuda\n"
                "/suscribirse - activar notificaciones de cursos\n"
                "/desuscribirse - pausar notificaciones de cursos\n"
                "/filtros - ver y cambiar los filtros de búsqueda"
            ),
        )
