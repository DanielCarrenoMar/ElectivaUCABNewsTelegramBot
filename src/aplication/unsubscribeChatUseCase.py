import logging

from domain.repository.databaseRepository import DatabaseRepository


class UnsubscribeChatUseCase:
    def __init__(self, databaseRepository: DatabaseRepository):
        self._databaseRepository = databaseRepository

    def execute(self, chatId: int) -> None:
        self._databaseRepository.getOrCreateChatConfig(chatId)
        self._databaseRepository.updateChatSubscription(chatId, False)
        logging.info("UnsubscribeChatUseCase: el chat %s se desuscribió de las notificaciones", chatId)