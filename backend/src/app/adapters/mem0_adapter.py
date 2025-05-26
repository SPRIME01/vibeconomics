"""Memory adapter implementation using Mem0 client."""

from typing import Any

from mem0.client.main import MemoryClient
from pydantic import BaseModel, ValidationError


class Mem0Memory(BaseModel):
    """Pydantic model for a memory item returned by Mem0."""

    id: str
    memory: str
    metadata: dict[str, Any] | None = None
    score: float | None = None


class Mem0Adapter:
    """Adapter for Mem0 memory management service."""

    _client: MemoryClient

    def __init__(self) -> None:
        """Initialize the Mem0 adapter with a client instance."""
        try:
            self._client = MemoryClient()
        except Exception as e:
            # Log error: "Failed to initialize Mem0Client"
            # Consider how to handle this critical failure,
            # maybe raise a custom AdapterInitializationError
            raise RuntimeError(f"Failed to initialize Mem0Client: {e}") from e

    def add(
        self, user_id: str, text_content: str, metadata: dict[str, Any] | None = None
    ) -> str | None:
        """Add a memory item and return its ID.

        Args:
            user_id: The user identifier
            text_content: The text content to store
            metadata: Optional metadata dictionary

        Returns:
            The ID of the stored memory item, or None if an error occurs.
        """
        try:
            response = self._client.add(
                messages=[{"role": "user", "content": text_content}],
                user_id=user_id,
                metadata=metadata,
            )
            if isinstance(response, dict) and "id" in response:
                return response["id"]
            # Log error: "Mem0 client add returned unexpected response format"
            return None
        except Exception:
            # Log error: "Error adding memory item to Mem0"
            return None

    def search(
        self, user_id: str, query: str, limit: int | None = None
    ) -> list[Mem0Memory]:
        """Search for memory items.

        Args:
            user_id: The user identifier
            query: The search query
            limit: Optional limit on number of results

        Returns:
            List of Mem0Memory objects, or an empty list if an error occurs or no items are found.
        """
        try:
            results = self._client.search(
                query=query,
                user_id=user_id,
                limit=limit,
            )
            parsed_results: list[Mem0Memory] = []
            if isinstance(results, list):
                for item in results:
                    if isinstance(item, dict):
                        try:
                            parsed_results.append(Mem0Memory.model_validate(item))
                        except ValidationError:
                            # Log warning: "Failed to validate memory item from search results"
                            pass  # Skip malformed items
            return parsed_results
        except Exception:
            # Log error: "Error searching memory items in Mem0"
            return []

    def get(self, memory_id: str) -> Mem0Memory | None:
        """Get a specific memory item by ID.

        Args:
            memory_id: The memory item identifier

        Returns:
            A Mem0Memory object if found, None otherwise.
        """
        try:
            item = self._client.get(memory_id)
            if isinstance(item, dict):
                return Mem0Memory.model_validate(item)
            return None
        except ValidationError:
            # Log warning: "Failed to validate memory item from get response"
            return None
        except Exception:
            # Log error: "Error getting memory item from Mem0"
            return None

    def update(self, memory_id: str, data: dict[str, Any]) -> Mem0Memory | None:
        """Update a memory item.

        Args:
            memory_id: The memory item identifier
            data: The updated data

        Returns:
            The updated Mem0Memory object if successful, None otherwise.
        """
        try:
            updated_item = self._client.update(memory_id, data)
            if isinstance(updated_item, dict):
                # Ensure the response includes 'id' and 'memory' for successful validation
                # The mem0 client's update might return the full updated object or just a status.
                # Assuming it returns the full object for now.
                # If 'id' or 'memory' is missing, model_validate will fail.
                return Mem0Memory.model_validate(updated_item)
            return None
        except ValidationError:
            # Log warning: "Failed to validate memory item from update response"
            return None
        except Exception:
            # Log error: "Error updating memory item in Mem0"
            return None

    def delete(self, memory_id: str) -> bool:
        """Delete a memory item.

        Args:
            memory_id: The memory item identifier

        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            self._client.delete(memory_id)
            return True
        except Exception:
            # Log error: "Error deleting memory item in Mem0"
            return False
