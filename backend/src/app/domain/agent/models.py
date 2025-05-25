from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.core.base_aggregate import AggregateRoot, DomainEvent

class ChatMessage(BaseModel):
    role: str # "user", "assistant", "system"
    content: str

class Conversation(AggregateRoot[UUID]):
    # id is inherited from AggregateRoot
    user_id: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)
    # created_at: datetime = Field(default_factory=datetime.utcnow)
    # last_updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str) -> None:
        msg = ChatMessage(role=role, content=content)
        self.messages.append(msg)
        # self.add_event(ConversationMessageAddedEvent(conversation_id=self.id, role=role, content_preview=content[:50]))
