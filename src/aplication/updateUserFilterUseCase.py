import logging
from typing import Optional

from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp

CHAT_CONFIG_FIELD_BY_FILTER: dict[str, str] = {
    "country": "uniCountries",
    "university": "courseUniversity",
    "language": "uniLanguages",
    "course_level": "courseLevels",
    "disciplinary_field": "disciplinaryField",
}


class UpdateUserFilterUseCase:
    def __init__(self):
        self._databaseRepository = PostgresDatabaseRepositoryImp()

    def execute(self, chatId: int, filterKey: str, value: Optional[int]) -> None:
        field = CHAT_CONFIG_FIELD_BY_FILTER.get(filterKey)
        if field is None:
            raise ValueError(f"Filtro desconocido: {filterKey}")
        config = self._databaseRepository.getOrCreateChatConfig(chatId)
        setattr(config, field, value)
        self._databaseRepository.updateChatConfig(config)
        logging.info(
            "UpdateUserFilterUseCase: filtro %s del chat %s actualizado a %s",
            filterKey,
            chatId,
            value,
        )
