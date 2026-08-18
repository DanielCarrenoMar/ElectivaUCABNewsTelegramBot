import logging

from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


class UnsubscribeChatUseCase:
    def __init__(self):
        self._databaseRepository = PostgresDatabaseRepositoryImp()

    def execute(self, chatId: int) -> None:
        config = self._databaseRepository.getOrCreateChatConfig(chatId)
        config.isSubscribed = False
        self._databaseRepository.updateChatConfig(config)
        logging.info("UnsubscribeChatUseCase: el chat %s se desuscribió de las notificaciones", chatId)