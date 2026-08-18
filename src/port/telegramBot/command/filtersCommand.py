import logging
from typing import Optional

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.aplication.getUserFiltersUseCase import GetUserFiltersUseCase
from src.aplication.updateUserFilterUseCase import CHAT_CONFIG_FIELD_BY_FILTER, UpdateUserFilterUseCase
from src.config.defaultValuesCatalog import APP_COUNTRIES, APP_COURSE_LEVELS, APP_DISCIPLINARY_FIELDS, APP_LANGUAGES, APP_UNIVERSITIES
from src.domain.model.chatConfigModel import ChatConfig

FILTER_CATALOGS: dict[str, tuple[str, dict[str, str]]] = {
    "country": ("🌍 País", APP_COUNTRIES),
    "language": ("🗣️ Idioma", APP_LANGUAGES),
    "course_level": ("📚 Nivel del curso", APP_COURSE_LEVELS),
    "disciplinary_field": ("🧠 Área disciplinaria", APP_DISCIPLINARY_FIELDS),
}


def _catalog_name(catalog: dict[str, str], filterId: Optional[int]) -> str:
    if filterId is None:
        return "Cualquiera"
    return catalog.get(str(filterId), f"Desconocido ({filterId})")


def _filters_text(config: ChatConfig) -> str:
    lines = ["<b>🎯 Tus filtros actuales</b>"]
    for filterKey, (label, catalog) in FILTER_CATALOGS.items():
        field = CHAT_CONFIG_FIELD_BY_FILTER[filterKey]
        lines.append(f"• {label}: {_catalog_name(catalog, getattr(config, field))}")
    lines.append("")
    lines.append("Selecciona un filtro para cambiarlo:")
    return "\n".join(lines)


def _filters_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    for filterKey, (label, _) in FILTER_CATALOGS.items():
        keyboard.add(InlineKeyboardButton(label, callback_data=f"filtro:{filterKey}"))
    return keyboard


def _options_keyboard(filterKey: str, catalog: dict[str, str], currentId: Optional[int]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    for filterId, name in catalog.items():
        buttonName = name
        if currentId is not None and int(filterId) == currentId:
            buttonName = f"✅ {name}"
        keyboard.add(InlineKeyboardButton(buttonName, callback_data=f"filtro_valor:{filterKey}:{filterId}"))
    keyboard.add(
        InlineKeyboardButton("🎲 Cualquiera", callback_data=f"filtro_valor:{filterKey}:none"),
        InlineKeyboardButton("⬅️ Volver", callback_data="filtros"),
    )
    return keyboard


def _safe_edit(bot, text: str, chatId: int, messageId: int, keyboard: InlineKeyboardMarkup) -> None:
    try:
        bot.edit_message_text(text, chatId, messageId, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        if "message is not modified" in str(e):
            return
        raise


def register(bot):
    getUserFiltersUseCase = GetUserFiltersUseCase()
    updateUserFilterUseCase = UpdateUserFilterUseCase()

    @bot.message_handler(commands=["filtros"])
    def handle_filters(message):
        try:
            config = getUserFiltersUseCase.execute(message.chat.id)
            bot.send_message(message.chat.id, _filters_text(config), parse_mode="HTML", reply_markup=_filters_keyboard())
        except Exception:
            logging.exception("filtersCommand: error al mostrar filtros del chat %s", message.chat.id)
            bot.reply_to(message, "❌ Ocurrió un error al consultar tus filtros. Inténtalo más tarde.")

    @bot.callback_query_handler(func=lambda call: call.data == "filtros")
    def handle_back(call):
        try:
            config = getUserFiltersUseCase.execute(call.message.chat.id)
            _safe_edit(bot, _filters_text(config), call.message.chat.id, call.message.message_id, _filters_keyboard())
            bot.answer_callback_query(call.id)
        except Exception:
            logging.exception("filtersCommand: error al volver al resumen de filtros del chat %s", call.message.chat.id)
            bot.answer_callback_query(call.id, "❌ No se pudo actualizar el mensaje.", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("filtro:"))
    def handle_filter_selection(call):
        filterKey = call.data.split(":")[1]
        if filterKey not in FILTER_CATALOGS:
            bot.answer_callback_query(call.id, "❌ Filtro no válido.", show_alert=True)
            return
        try:
            config = getUserFiltersUseCase.execute(call.message.chat.id)
            label, catalog = FILTER_CATALOGS[filterKey]
            currentId = getattr(config, CHAT_CONFIG_FIELD_BY_FILTER[filterKey])
            text = f"<b>{label}</b>\nActual: {_catalog_name(catalog, currentId)}\n\nElige el nuevo valor:"
            _safe_edit(bot, text, call.message.chat.id, call.message.message_id, _options_keyboard(filterKey, catalog, currentId))
            bot.answer_callback_query(call.id)
        except Exception:
            logging.exception("filtersCommand: error al mostrar opciones del filtro %s del chat %s", filterKey, call.message.chat.id)
            bot.answer_callback_query(call.id, "❌ No se pudo actualizar el mensaje.", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("filtro_valor:"))
    def handle_value_selection(call):
        parts = call.data.split(":")
        filterKey = parts[1]
        rawValue = parts[2]
        if filterKey not in FILTER_CATALOGS:
            bot.answer_callback_query(call.id, "❌ Filtro no válido.", show_alert=True)
            return
        try:
            newValue = None if rawValue == "none" else int(rawValue)
        except ValueError:
            bot.answer_callback_query(call.id, "❌ Valor no válido.", show_alert=True)
            return
        try:
            updateUserFilterUseCase.execute(call.message.chat.id, filterKey, newValue)
            config = getUserFiltersUseCase.execute(call.message.chat.id)
            _safe_edit(bot, _filters_text(config), call.message.chat.id, call.message.message_id, _filters_keyboard())
            bot.answer_callback_query(call.id, "✅ Filtro actualizado")
        except Exception:
            logging.exception("filtersCommand: error al actualizar filtro %s del chat %s", filterKey, call.message.chat.id)
            bot.answer_callback_query(call.id, "❌ Ocurrió un error al actualizar el filtro.", show_alert=True)