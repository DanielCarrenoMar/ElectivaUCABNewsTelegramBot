import logging

from src.infraestructure.repositoryImp.postgresDatabaseRepositoryImp import PostgresDatabaseRepositoryImp


class SubscribeChatUseCase:
    def __init__(self):
        self._databaseRepository = PostgresDatabaseRepositoryImp()

    def execute(self, chatId: int) -> None:
        self._databaseRepository.getOrCreateChatConfig(chatId)
        self._databaseRepository.updateChatSubscription(chatId, True)
        logging.info("SubscribeChatUseCase: el chat %s se suscribió a las notificaciones", chatId)