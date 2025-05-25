from typing import Any

from app.core.base_aggregate import AggregateId, DomainEvent


class MemoryEvent(DomainEvent):
    """Base class for memory-related domain events."""

    memory_id: AggregateId  # Changed from MemoryId to AggregateId to match base DomainEvent if needed
    user_id: str


class MemoryStoredEvent(MemoryEvent):
    """Event published when a new memory is successfully stored."""

    text_content_preview: str  # e.g., first 100 chars
    metadata: dict[str, Any] | None = None
    external_id: str | None = None  # ID from the external memory system (e.g., Mem0)


class MemoryRetrievalFailedEvent(MemoryEvent):
    """Event published when memory retrieval fails."""

    error_message: str
    query_details: dict[str, Any] | None = None  # e.g., search text, filters used
