from uuid import UUID

from pydantic import BaseModel, Field

from app.core.base_aggregate import AggregateRoot


class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str


class Conversation(AggregateRoot[UUID]):
    # id is inherited from AggregateRoot
    user_id: str | None = None
    messages: list[ChatMessage] = Field(default_factory=list)
    # created_at: datetime = Field(default_factory=datetime.utcnow)
    # last_updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str) -> None:
        msg = ChatMessage(role=role, content=content)
        self.messages.append(msg)
        # self.add_event(ConversationMessageAddedEvent(conversation_id=self.id, role=role, content_preview=content[:50]))
