from src.domain.model.chatConfigModel import ChatConfig
from src.infraestructure.dto.database.chatConfigsDto import ChatConfigsDto


def chatConfigToChatConfigsDto(chatConfig: ChatConfig) -> ChatConfigsDto:
    return ChatConfigsDto(
        id=chatConfig.id,
        is_subscribed=chatConfig.isSubscribed,
        last_revision=chatConfig.lastRevision,
        uni_countries=chatConfig.uniCountries,
        disciplinary_field=chatConfig.disciplinaryField,
        course_university=chatConfig.courseUniversity,
        uni_languages=chatConfig.uniLanguages,
        course_levels=chatConfig.courseLevels,
        key_word=chatConfig.keyWord,
    )
