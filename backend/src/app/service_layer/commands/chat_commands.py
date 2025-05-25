from typing import List, Dict, Any, Optional, Type, Callable, AsyncGenerator, Protocol
from uuid import UUID
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from app.core.base_aggregate import DomainEvent # Adjusted import

class ProcessUserChatMessageCommand(BaseModel):
    session_id: Optional[UUID] = None
    user_id: Optional[str] = None
    message_content: str
    model_name: Optional[str] = None
    # Add other relevant fields
