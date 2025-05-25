from typing import List, Dict, Any, Optional, Type, Callable, AsyncGenerator, Protocol
from uuid import UUID
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from app.core.base_aggregate import DomainEvent # Adjusted import

class StoreMemoryCommand(BaseModel):
    user_id: str
    text_content: str
    metadata: Optional[Dict[str, Any]] = None
