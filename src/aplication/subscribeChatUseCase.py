import logging

from src.domain.databaseRepository import DatabaseRepository


class SubscribeChatUseCase:
    def __init__(self, databaseRepository: DatabaseRepository):
        self._databaseRepository = databaseRepository

    def execute(self, chatId: int) -> None:
        self._databaseRepository.getOrCreateChatConfig(chatId)
        self._databaseRepository.updateChatSubscription(chatId, True)
        logging.info("SubscribeChatUseCase: el chat %s se suscribió a las notificaciones", chatId)