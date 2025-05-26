from typing import Protocol
from uuid import UUID

from app.domain.agent.models import Conversation


class AbstractConversationRepository(Protocol):
    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        """Retrieves a Conversation by its ID."""
        ...

    async def save(self, conversation: Conversation) -> None:
        """Saves a Conversation. Handles both creation of new conversations and updates to existing ones."""
        ...

    async def create(self, conversation: Conversation) -> None:
        """Creates a new Conversation. Should raise an error if it already exists."""
        ...
