from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.core.base_aggregate import AggregateRoot, DomainEvent

class ConversationMessageAddedEvent(DomainEvent):
    conversation_id: UUID
    role: str
    content_preview: str
