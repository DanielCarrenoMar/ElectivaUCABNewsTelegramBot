import logging

from src.domain.model.chatConfigModel import ChatConfig
from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


class GetUserFiltersUseCase:
    def __init__(self):
        self._databaseRepository = PostgresDatabaseRepositoryImp()

    def execute(self, chatId: int) -> ChatConfig:
        config = self._databaseRepository.getOrCreateChatConfig(chatId)
        logging.info("GetUserFiltersUseCase: filtros del chat %s obtenidos", chatId)
        return config