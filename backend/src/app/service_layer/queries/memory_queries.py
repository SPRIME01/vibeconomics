from typing import List, Dict, Any, Optional, Type, Callable, AsyncGenerator, Protocol
from uuid import UUID
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from app.core.base_aggregate import DomainEvent # Adjusted import
# from app.domain.memory.models import MemoryQueryResult

class SearchMemoryQuery(BaseModel):
    user_id: str
    search_text: str
    limit: int = 10
