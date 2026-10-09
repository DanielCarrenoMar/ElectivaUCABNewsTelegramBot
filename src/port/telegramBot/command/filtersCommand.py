import logging
from typing import Callable, Dict, List, Optional

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.aplication.getUserFiltersUseCase import GetUserFiltersUseCase
from src.aplication.updateUserFilterUseCase import CHAT_CONFIG_FIELD_BY_FILTER, UpdateUserFilterUseCase
from src.domain.model.chatConfigModel import ChatConfig
from src.domain.model.courseModel import CatalogEntry
from src.domain.repository.coursesRepository import CoursesRepository
from src.infraestructure.repositoryImp.coursesRepositoryImp import CoursesRepositoryImp

# Cada dimensión del menú con su etiqueta y con el catálogo del que se alimenta. El
# valor que se guarda es la clave natural de la base de cursos (countries.iso_code,
# languages.code, academic_levels.id, knowledge_areas.name), no un id propio del bot:
# los catálogos son de otro sistema y el bot solo los lee.
# "university" sigue fuera del menú, igual que antes: la columna existe pero nunca
# se ofreció al usuario, así que tampoco se lee su catálogo.
FILTER_DIMENSIONS: dict[str, tuple[str, Callable[[CoursesRepository], List[CatalogEntry]]]] = {
    "country": ("🌍 País", lambda repository: repository.getCountryCatalog()),
    "language": ("🗣️ Idioma", lambda repository: repository.getLanguageCatalog()),
    "course_level": ("📚 Nivel del curso", lambda repository: repository.getAcademicLevelCatalog()),
    "disciplinary_field": ("🧠 Área disciplinaria", lambda repository: repository.getKnowledgeAreaCatalog()),
}


def _read_catalogs(
    coursesRepository: CoursesRepository, filterKeys: Optional[List[str]] = None
) -> Dict[str, List[CatalogEntry]]:
    """Lee una vez los catálogos pedidos, para un solo render.

    La conexión es un singleton cacheado, así que releer es barato; el motivo real
    es la consistencia: el teclado, la resolución del botón que se acaba de pulsar
    y los nombres del resumen tienen que salir todos de la misma versión del
    catálogo. Resolver contra otro catálogo guardaría un valor distinto del que el
    usuario vio en el botón.

    No se cachea entre invocaciones: si el sistema dueño publica una entrada nueva,
    el siguiente filtro ya debe ofrecerla.
    """
    keys = list(FILTER_DIMENSIONS) if filterKeys is None else filterKeys
    return {key: FILTER_DIMENSIONS[key][1](coursesRepository) for key in keys}


def _catalog_name(catalog: List[CatalogEntry], value: Optional[str]) -> str:
    if value is None:
        return "Cualquiera"
    for entry in catalog:
        if entry.value == value:
            return entry.label
    # El valor guardado ya no está en el catálogo. Decirlo es mejor que caer en
    # "Cualquiera": un filtro que se ensancha solo y en silencio es peor que uno
    # que el usuario sabe que está viejo, así que se muestra el valor tal cual.
    return f"⚠️ No disponible ({value})"


def _filters_text(config: ChatConfig, catalogs: Dict[str, List[CatalogEntry]]) -> str:
    lines = ["<b>Tus filtros actuales</b>"]
    for filterKey, (label, _) in FILTER_DIMENSIONS.items():
        field = CHAT_CONFIG_FIELD_BY_FILTER[filterKey]
        lines.append(f"• {label}: {_catalog_name(catalogs.get(filterKey, []), getattr(config, field))}")
    lines.append("")
    lines.append("Selecciona un filtro para cambiarlo:")
    return "\n".join(lines)


def _filters_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)
    for filterKey, (label, _) in FILTER_DIMENSIONS.items():
        keyboard.add(InlineKeyboardButton(label, callback_data=f"filtro:{filterKey}"))
    return keyboard


def _options_keyboard(filterKey: str, catalog: List[CatalogEntry], currentValue: Optional[str]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=2)
    for index, entry in enumerate(catalog):
        buttonName = entry.label
        if currentValue is not None and entry.value == currentValue:
            buttonName = f"✅ {entry.label}"
        # El botón lleva el índice del catálogo, no el valor. Telegram rechaza todo
        # callback_data de más de 64 bytes, y con los nombres nuevos tres áreas de
        # conocimiento lo pasaban ("Otra Ciencia económico-administrativa" llegaba a
        # 70 bytes), es decir, no se podían elegir. Con el índice el callback más
        # largo queda en 34 bytes por más largo que sea el nombre, y la etiqueta se
        # muestra completa: nada de truncar. El valor real se resuelve contra el
        # catálogo al pulsar.
        keyboard.add(InlineKeyboardButton(buttonName, callback_data=f"filtro_valor:{filterKey}:{index}"))
    keyboard.add(
        InlineKeyboardButton("🎲 Cualquiera", callback_data=f"filtro_valor:{filterKey}:none"),
        InlineKeyboardButton("⬅️ Volver", callback_data="filtros"),
    )
    return keyboard


def _entry_at_index(catalog: List[CatalogEntry], rawIndex: str) -> Optional[CatalogEntry]:
    """Entrada del catálogo que corresponde al índice del botón, o None si no vale.

    Un índice no numérico o fuera de rango no es un error de programación sino un
    botón viejo: el teclado se quedó pegado al mensaje de Telegram y el catálogo
    pudo cambiar desde que se dibujó. Se devuelve None para responder con un aviso
    en vez de guardar un valor equivocado o dejar que reviente el handler.
    """
    try:
        index = int(rawIndex)
    except ValueError:
        return None
    if index < 0 or index >= len(catalog):
        return None
    return catalog[index]


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
    coursesRepository = CoursesRepositoryImp()

    @bot.message_handler(commands=["filtros"])
    def handle_filters(message):
        try:
            config = getUserFiltersUseCase.execute(message.chat.id)
            catalogs = _read_catalogs(coursesRepository)
            bot.send_message(message.chat.id, _filters_text(config, catalogs), parse_mode="HTML", reply_markup=_filters_keyboard())
        except Exception:
            logging.exception("filtersCommand: error al mostrar filtros del chat %s", message.chat.id)
            bot.reply_to(message, "❌ Ocurrió un error al consultar tus filtros. Inténtalo más tarde.")

    @bot.callback_query_handler(func=lambda call: call.data == "filtros")
    def handle_back(call):
        try:
            config = getUserFiltersUseCase.execute(call.message.chat.id)
            catalogs = _read_catalogs(coursesRepository)
            _safe_edit(bot, _filters_text(config, catalogs), call.message.chat.id, call.message.message_id, _filters_keyboard())
            bot.answer_callback_query(call.id)
        except Exception:
            logging.exception("filtersCommand: error al volver al resumen de filtros del chat %s", call.message.chat.id)
            bot.answer_callback_query(call.id, "❌ No se pudo actualizar el mensaje.", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("filtro:"))
    def handle_filter_selection(call):
        filterKey = call.data.split(":")[1]
        if filterKey not in FILTER_DIMENSIONS:
            bot.answer_callback_query(call.id, "❌ Filtro no válido.", show_alert=True)
            return
        try:
            config = getUserFiltersUseCase.execute(call.message.chat.id)
            label = FILTER_DIMENSIONS[filterKey][0]
            # Solo hace falta el catálogo de esta dimensión: es el que dibuja el
            # teclado y el que resuelve el "Actual:".
            catalog = _read_catalogs(coursesRepository, [filterKey])[filterKey]
            currentValue = getattr(config, CHAT_CONFIG_FIELD_BY_FILTER[filterKey])
            text = f"<b>{label}</b>\nActual: {_catalog_name(catalog, currentValue)}\n\nElige el nuevo valor:"
            _safe_edit(bot, text, call.message.chat.id, call.message.message_id, _options_keyboard(filterKey, catalog, currentValue))
            bot.answer_callback_query(call.id)
        except Exception:
            logging.exception("filtersCommand: error al mostrar opciones del filtro %s del chat %s", filterKey, call.message.chat.id)
            bot.answer_callback_query(call.id, "❌ No se pudo actualizar el mensaje.", show_alert=True)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("filtro_valor:"))
    def handle_value_selection(call):
        parts = call.data.split(":")
        filterKey = parts[1]
        rawIndex = parts[2] if len(parts) > 2 else ""
        if filterKey not in FILTER_DIMENSIONS:
            bot.answer_callback_query(call.id, "❌ Filtro no válido.", show_alert=True)
            return
        # Un solo volcado de catálogos para toda la pulsación: resuelve el índice
        # del botón y de paso rotula el resumen al que se vuelve.
        try:
            catalogs = _read_catalogs(coursesRepository)
        except Exception:
            logging.exception("filtersCommand: error al leer el catálogo del filtro %s del chat %s", filterKey, call.message.chat.id)
            bot.answer_callback_query(call.id, "❌ No se pudo consultar el catálogo. Inténtalo más tarde.", show_alert=True)
            return

        if rawIndex == "none":
            newValue = None
        else:
            entry = _entry_at_index(catalogs[filterKey], rawIndex)
            if entry is None:
                logging.warning(
                    "filtersCommand: índice de catálogo inválido %r para el filtro %s del chat %s",
                    rawIndex,
                    filterKey,
                    call.message.chat.id,
                )
                bot.answer_callback_query(call.id, "❌ Esa opción ya no está disponible. Vuelve a abrir tus filtros.", show_alert=True)
                return
            newValue = entry.value
        try:
            updateUserFilterUseCase.execute(call.message.chat.id, filterKey, newValue)
            config = getUserFiltersUseCase.execute(call.message.chat.id)
            _safe_edit(bot, _filters_text(config, catalogs), call.message.chat.id, call.message.message_id, _filters_keyboard())
            bot.answer_callback_query(call.id, "✅ Filtro actualizado")
        except Exception:
            logging.exception("filtersCommand: error al actualizar filtro %s del chat %s", filterKey, call.message.chat.id)
            bot.answer_callback_query(call.id, "❌ Ocurrió un error al actualizar el filtro.", show_alert=True)