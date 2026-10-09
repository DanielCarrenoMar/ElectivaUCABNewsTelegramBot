from typing import Mapping, Optional

from src.domain.model.chatConfigModel import ChatConfig
from src.infraestructure.dto.database.chatConfigsDto import ChatConfigsDto


def chatConfigToChatConfigsDto(chatConfig: ChatConfig) -> ChatConfigsDto:
    """Convierte la configuración del chat en la fila que se guarda en chatconfigs."""
    return ChatConfigsDto(
        id=chatConfig.id,
        is_subscribed=chatConfig.isSubscribed,
        last_revision=chatConfig.lastRevision,
        country_iso_code=chatConfig.countryIsoCode,
        course_university=chatConfig.courseUniversity,
        course_language_code=chatConfig.courseLanguageCode,
        course_level_id=chatConfig.courseLevelId,
        disciplinary_field=chatConfig.disciplinaryField,
        key_word=chatConfig.keyWord,
    )


def chatConfigsDtoToChatConfig(row: Mapping[str, object]) -> ChatConfig:
    """Convierte una fila de chatconfigs leida de la base en su ChatConfig.

    La columna lastrevision se lee como last_revision porque asi se llama el campo
    en el DTO. El id y la suscripcion son NOT NULL en la tabla, asi que se exigen.
    """
    chatId = row.get("id")
    if chatId is None:
        raise ValueError("La fila de chatconfigs no trae el id del chat")

    return ChatConfig(
        id=int(chatId),
        isSubscribed=bool(row.get("is_subscribed", True)),
        lastRevision=_optionalText(row.get("last_revision")),
        countryIsoCode=_optionalText(row.get("country_iso_code")),
        courseUniversity=_optionalText(row.get("course_university")),
        courseLanguageCode=_optionalText(row.get("course_language_code")),
        courseLevelId=_optionalText(row.get("course_level_id")),
        disciplinaryField=_optionalText(row.get("disciplinary_field")),
        keyWord=_optionalText(row.get("key_word")),
    )


def _optionalText(value: Optional[object]) -> Optional[str]:
    """Normaliza un valor de filtro: vacio o solo espacios significa "sin filtro"."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None