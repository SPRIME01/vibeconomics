from dataclasses import dataclass
from uuid import UUID

from app.core.base_aggregate import DomainEvent  # Changed from app.core.base_event


@dataclass(frozen=True)
class ConversationMessageAddedEvent(DomainEvent):
    conversation_id: UUID
    role: str
    content_preview: str
