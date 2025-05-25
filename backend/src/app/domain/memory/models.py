import uuid
from typing import Any, NewType

from pydantic import BaseModel, Field

from app.core.base_aggregate import AggregateId, AggregateRoot, DomainEvent

MemoryId = NewType("MemoryId", AggregateId)


class MemoryMetadata(BaseModel):
    """Represents metadata associated with a memory item."""

    pass


class MemoryWriteRequest(BaseModel):
    """Represents a request to write (create or update) a memory."""

    user_id: str = Field(..., description="ID of the user associated with the memory.")
    text_content: str = Field(..., description="The textual content of the memory.")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata."
    )  # Corrected default


class MemoryItem(AggregateRoot[DomainEvent]):
    """
    Represents a memory item in the domain.
    This is an aggregate root.
    """

    user_id: str
    text_content: str
    metadata: MemoryMetadata
    _mem0_id: str | None = Field(default=None, alias="mem0_id")

    def __init__(
        self,
        id: MemoryId,
        user_id: str,
        text_content: str,
        metadata: dict[str, Any] | None = None,
        mem0_id: str | None = None,
        **data: Any,
    ) -> None:
        """Initializes MemoryItem."""
        super().__init__(id)
        self.user_id = user_id
        self.text_content = text_content
        self.metadata = MemoryMetadata(**(metadata or {}))
        self._mem0_id = mem0_id

    @classmethod
    def create(
        cls,
        user_id: str,
        text_content: str,
        metadata: dict[str, Any] | None = None,
        memory_id: MemoryId | None = None,
        external_mem_id: str | None = None,
    ) -> "MemoryItem":
        """Factory method to create a new MemoryItem."""
        # Corrected MemoryId creation and removed type: ignore
        agg_id = memory_id if memory_id else MemoryId(AggregateId(uuid.uuid4()))
        item = cls(
            id=agg_id,
            user_id=user_id,
            text_content=text_content,
            metadata=metadata,
            mem0_id=external_mem_id,
        )
        return item

    def update_content(
        self, text_content: str, new_metadata: dict[str, Any] | None = None
    ) -> None:
        """Updates content and optionally metadata."""
        self.text_content = text_content
        if new_metadata is not None:
            self.metadata = MemoryMetadata(**new_metadata)
        self.version += 1

    @property
    def mem0_id(self) -> str | None:
        """Accessor for the external Mem0 ID."""
        return self._mem0_id


class MemorySearchResultItem(BaseModel):
    """Represents a single search result item."""

    id: str
    text_content: str
    metadata: dict[str, Any] | None = None
    score: float | None = None


class MemoryQuery(BaseModel):
    """Represents a query to search memories."""

    user_id: str = Field(..., description="ID of the user whose memories to search.")
    search_text: str = Field(..., description="The text to search for in memories.")
    limit: int | None = Field(
        default=10, description="Maximum number of results to return."
    )


class MemoryQueryResult(BaseModel):
    """Represents the result of a memory search query."""

    query: MemoryQuery
    results: list[MemorySearchResultItem] = Field(default_factory=list)
