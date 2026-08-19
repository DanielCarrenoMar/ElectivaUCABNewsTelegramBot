import logging

from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


class SubscribeChatUseCase:
    def __init__(self):
        self._databaseRepository = PostgresDatabaseRepositoryImp()

    def execute(self, chatId: int) -> None:
        config = self._databaseRepository.getOrCreateChatConfig(chatId)
        config.isSubscribed = True
        self._databaseRepository.updateChatConfig(config)
        logging.info("SubscribeChatUseCase: el chat %s se suscribió a las notificaciones", chatId)