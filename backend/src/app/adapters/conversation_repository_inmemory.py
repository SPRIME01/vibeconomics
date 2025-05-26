from uuid import UUID

from app.domain.agent.models import Conversation
from app.domain.agent.ports import AbstractConversationRepository


class ConversationAlreadyExistsError(Exception):
    pass


class InMemoryConversationRepository(AbstractConversationRepository):
    def __init__(self) -> None:
        self._conversations: dict[UUID, Conversation] = {}

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        conversation = self._conversations.get(conversation_id)
        if conversation:
            return conversation.model_copy(deep=True)
        return None

    async def create(self, conversation: Conversation) -> None:
        if conversation.id in self._conversations:
            raise ConversationAlreadyExistsError(
                f"Conversation with ID {conversation.id} already exists."
            )
        self._conversations[conversation.id] = conversation.model_copy(deep=True)

    async def save(self, conversation: Conversation) -> None:
        self._conversations[conversation.id] = conversation.model_copy(deep=True)
