from abc import ABC, abstractmethod
from typing import Any  # Added Dict

from app.adapters.mem0_adapter import (
    AbstractMemoryAdapter,
    MemorySearchRequest,
    MemorySearchResult,
    MemoryWriteRequest,
)


class AbstractMemoryService(ABC):
    """Abstract interface for memory operations."""

    @abstractmethod
    def search(
        self, user_id: str, query: str, limit: int = 5
    ) -> list[MemorySearchResult]:  # Changed return type
        """Search memories for a user."""
        pass

    @abstractmethod
    def add(
        self, user_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> str | None:
        """Add a memory for a user."""
        pass


class MemoryService(AbstractMemoryService):  # Inherit from AbstractMemoryService
    """Service for managing user memories via Mem0."""

    def __init__(
        self, mem0_adapter: AbstractMemoryAdapter
    ) -> None:  # Use AbstractMemoryAdapter
        self._mem0_adapter = mem0_adapter

    def search(
        self, user_id: str, query: str, limit: int = 5
    ) -> list[MemorySearchResult]:  # Changed return type
        """
        Search memories for a user.

        Args:
            user_id: User ID to search memories for
            query: Search query
            limit: Maximum number of results to return

        Returns:
            List of memory search results
        """
        try:
            request = MemorySearchRequest(user_id=user_id, query=query, limit=limit)
            return self._mem0_adapter.search(request)
        except Exception as e:
            # Log error and return empty list
            import logging

            logging.exception(f"Error searching memories: {e}")
            return []

    def add(
        self, user_id: str, content: str, metadata: dict[str, Any] | None = None
    ) -> str | None:
        """
        Add a memory for a user.

        Args:
            user_id: User ID
            content: Memory content
            metadata: Optional metadata

        Returns:
            Memory ID if successful, None otherwise
        """
        try:
            request = MemoryWriteRequest(
                user_id=user_id, text_content=content, metadata=metadata
            )
            return self._mem0_adapter.add(request)
        except Exception as e:
            # Log error and return None
            import logging

            logging.exception(f"Error adding memory: {e}")
            return None
