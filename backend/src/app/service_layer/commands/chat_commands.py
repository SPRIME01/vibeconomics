from uuid import UUID

from pydantic import BaseModel


class ProcessUserChatMessageCommand(BaseModel):
    session_id: UUID | None = None
    user_id: str | None = None
    message_content: str
    model_name: str | None = None
    # Add other relevant fields
