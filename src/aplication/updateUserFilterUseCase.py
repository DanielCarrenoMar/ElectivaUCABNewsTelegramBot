import logging
from typing import Optional

from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp

# Cada filtro del teclado apunta al atributo de ChatConfig que lo guarda. El valor ya
# no es un id propio sino la clave natural del catalogo de cursos (iso_code, name,
# code, academic_levels.id), asi que llega como texto.
CHAT_CONFIG_FIELD_BY_FILTER: dict[str, str] = {
    "country": "countryIsoCode",
    "university": "courseUniversity",
    "language": "courseLanguageCode",
    "course_level": "courseLevelId",
    "disciplinary_field": "disciplinaryField",
    "key_word": "keyWord",
}


class UpdateUserFilterUseCase:
    def __init__(self):
        self._databaseRepository = PostgresDatabaseRepositoryImp()

    def execute(self, chatId: int, filterKey: str, value: Optional[str]) -> None:
        field = CHAT_CONFIG_FIELD_BY_FILTER.get(filterKey)
        if field is None:
            raise ValueError(f"Filtro desconocido: {filterKey}")

        # Un valor vacio equivale a "cualquiera": se guarda como NULL, que es lo que
        # el emparejamiento de cursos interpreta como filtro ausente.
        newValue = value.strip() if isinstance(value, str) and value.strip() else None

        config = self._databaseRepository.getOrCreateChatConfig(chatId)
        setattr(config, field, newValue)
        self._databaseRepository.updateChatConfig(config)
        logging.info(
            "UpdateUserFilterUseCase: filtro %s del chat %s actualizado a %s",
            filterKey,
            chatId,
            newValue,
        )