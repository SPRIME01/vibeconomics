"""Memory adapter implementation using Mem0 client."""

import logging
from typing import Any, Protocol

from pydantic import BaseModel


class MemoryWriteRequest(BaseModel):
    """Request model for adding memories."""

    user_id: str
    text_content: str
    metadata: dict[str, Any] | None = None


class MemorySearchRequest(BaseModel):
    """Request model for searching memories."""

    user_id: str
    query: str
    limit: int | None = 5
    min_score: float | None = None


class MemorySearchResult(BaseModel):
    """Result model for memory search."""

    id: str
    content: str
    score: float
    metadata: dict[str, Any] | None = None


class AbstractMemoryAdapter(Protocol):
    """Port/interface for memory operations."""

    def add(self, request: MemoryWriteRequest) -> str | None:
        """Add a memory and return its ID."""
        ...

    def search(self, request: MemorySearchRequest) -> list[MemorySearchResult]:
        """Search memories and return results."""
        ...


class Mem0Adapter:
    """Concrete adapter for Mem0 memory service."""

    def __init__(self, client: Any) -> None:
        """Initialize with mem0 client."""
        self._client = client
        self._logger = logging.getLogger(__name__)

    def add(self, request: MemoryWriteRequest) -> str | None:
        """Add a memory to Mem0."""
        try:
            # When mem0 client is available, this would be:
            # response = self._client.add(
            #     user_id=request.user_id,
            #     text=request.text_content,
            #     metadata=request.metadata
            # )
            # return response.get("id")

            # Mock implementation for now
            self._logger.info(f"Adding memory for user {request.user_id}")
            return f"memory_{request.user_id}_{hash(request.text_content)}"

        except Exception as e:
            self._logger.exception(f"Error adding memory: {e}")
            return None

    def search(self, request: MemorySearchRequest) -> list[MemorySearchResult]:
        """Search memories in Mem0."""
        try:
            # When mem0 client is available, this would be:
            # results = self._client.search(
            #     user_id=request.user_id,
            #     query=request.query,
            #     limit=request.limit
            # )
            # return [
            #     MemorySearchResult(
            #         id=res["id"],
            #         content=res["text"],
            #         score=res["score"],
            #         metadata=res.get("metadata")
            #     ) for res in results
            # ]

            # Mock implementation for now
            self._logger.info(f"Searching memories for user {request.user_id}")
            return [
                MemorySearchResult(
                    id="mock_1",
                    content="Mock memory result 1",
                    score=0.9,
                    metadata={"source": "mock"},
                ),
                MemorySearchResult(
                    id="mock_2",
                    content="Mock memory result 2",
                    score=0.8,
                    metadata={"source": "mock"},
                ),
            ]

        except Exception as e:
            self._logger.exception(f"Error searching memories: {e}")
            return []


class FakeMemoryAdapter:
    """Fake adapter for testing."""

    def __init__(self) -> None:
        self._memories: dict[str, list[dict[str, Any]]] = {}
        self._next_id = 1

    def add(self, request: MemoryWriteRequest) -> str | None:
        """Add memory to in-memory storage."""
        memory_id = f"fake_memory_{self._next_id}"
        self._next_id += 1

        if request.user_id not in self._memories:
            self._memories[request.user_id] = []

        self._memories[request.user_id].append(
            {
                "id": memory_id,
                "content": request.text_content,
                "metadata": request.metadata or {},
            }
        )

        return memory_id

    def search(self, request: MemorySearchRequest) -> list[MemorySearchResult]:
        """Search memories in fake storage."""
        user_memories = self._memories.get(request.user_id, [])

        # Simple text matching for fake implementation
        results = []
        for memory in user_memories:
            if request.query.lower() in memory["content"].lower():
                score = (
                    0.9 if request.query.lower() == memory["content"].lower() else 0.7
                )
                results.append(
                    MemorySearchResult(
                        id=memory["id"],
                        content=memory["content"],
                        score=score,
                        metadata=memory["metadata"],
                    )
                )

        # Apply limit
        if request.limit:
            results = results[: request.limit]

        return results
