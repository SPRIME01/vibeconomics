"""Memory adapter implementation using Mem0 client."""

from typing import Any

from mem0.client.main import MemoryClient  # Updated import


class Mem0Adapter:
    """Adapter for Mem0 memory management service."""

    def __init__(self) -> None:
        """Initialize the Mem0 adapter with a client instance."""
        self._client = MemoryClient()  # Use the correct class name

    def add(
        self, user_id: str, text_content: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """Add a memory item and return its ID.

        Args:
            user_id: The user identifier
            text_content: The text content to store
            metadata: Optional metadata dictionary

        Returns:
            The ID of the stored memory item
        """
        response = self._client.add(
            messages=[{"role": "user", "content": text_content}],
            user_id=user_id,
            metadata=metadata,
        )
        return response["id"]

    def search(
        self, user_id: str, query: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Search for memory items.

        Args:
            user_id: The user identifier
            query: The search query
            limit: Optional limit on number of results

        Returns:
            List of search results
        """
        return self._client.search(
            query=query,
            user_id=user_id,
            limit=limit,
        )

    def get(self, memory_id: str) -> dict[str, Any] | None:
        """Get a specific memory item by ID.

        Args:
            memory_id: The memory item identifier

        Returns:
            The memory item if found, None otherwise
        """
        try:
            return self._client.get(memory_id)
        except Exception:
            return None

    def update(self, memory_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a memory item.

        Args:
            memory_id: The memory item identifier
            data: The updated data

        Returns:
            The updated memory item if successful, None otherwise
        """
        try:
            return self._client.update(memory_id, data)
        except Exception:
            return None

    def delete(self, memory_id: str) -> bool:
        """Delete a memory item.

        Args:
            memory_id: The memory item identifier

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            self._client.delete(memory_id)
            return True
        except Exception:
            return False
