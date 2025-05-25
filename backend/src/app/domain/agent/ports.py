from typing import Protocol
from uuid import UUID

from .models import Conversation  # Relative import


class AbstractConversationRepository(Protocol):
    async def get_by_id(self, conversation_id: UUID) -> Conversation | None: ...
    async def save(self, conversation: Conversation) -> None: ...
    async def add(
        self, conversation: Conversation
    ) -> None: ...  # Alias for save or specific create
