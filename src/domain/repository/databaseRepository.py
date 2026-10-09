from abc import ABC, abstractmethod
from typing import List

from src.domain.model.chatConfigModel import ChatConfig


class DatabaseRepository(ABC):
    """Contrato de la base de datos propia (DB_URL): suscripciones y filtros de chat."""

    @abstractmethod
    def getOrCreateChatConfig(self, chatId: int) -> ChatConfig:
        raise NotImplementedError

    @abstractmethod
    def getSubcriptorsChatConfig(self) -> List[ChatConfig]:
        raise NotImplementedError

    @abstractmethod
    def updateChatConfig(self, chatConfig: ChatConfig) -> None:
        raise NotImplementedError