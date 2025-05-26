from uuid import UUID

from app.core.base_event import DomainEvent


class ConversationMessageAddedEvent(DomainEvent):
    conversation_id: UUID
    role: str
    content_preview: str
