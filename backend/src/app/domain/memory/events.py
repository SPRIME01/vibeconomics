from dataclasses import dataclass
from datetime import datetime

from app.core.base_aggregate import DomainEvent


@dataclass(frozen=True)
class MemoryStoredEvent(DomainEvent):
    """Event raised when a memory is successfully stored."""

    memory_id: str
    user_id: str
    content: str
    metadata: dict | None = None
    timestamp: datetime | None = None
