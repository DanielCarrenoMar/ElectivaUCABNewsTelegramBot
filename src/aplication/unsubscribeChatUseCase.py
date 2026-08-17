import logging

from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


class UnsubscribeChatUseCase:
    def __init__(self):
        self._databaseRepository = PostgresDatabaseRepositoryImp()

    def execute(self, chatId: int) -> None:
        self._databaseRepository.getOrCreateChatConfig(chatId)
        self._databaseRepository.updateChatSubscription(chatId, False)
        logging.info("UnsubscribeChatUseCase: el chat %s se desuscribió de las notificaciones", chatId)