from typing import Protocol, Optional
from uuid import UUID
from .models import Conversation # Relative import

class AbstractConversationRepository(Protocol):
    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]: ...
    async def save(self, conversation: Conversation) -> None: ...
    async def add(self, conversation: Conversation) -> None: ... # Alias for save or specific create
