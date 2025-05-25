from typing import List, Dict, Any, Optional, Type, Callable, AsyncGenerator, Protocol
from uuid import UUID
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from app.core.base_aggregate import DomainEvent # Adjusted import
# from ..queries.memory_queries import SearchMemoryQuery
# from app.domain.memory.models import MemoryQueryResult
# from app.domain.memory.ports import AbstractMemoryRepository
