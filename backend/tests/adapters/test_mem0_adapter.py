"""Tests for Mem0 adapter implementation."""

from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.adapters.mem0_adapter import Mem0Adapter


class TestMem0Adapter:
    """Test suite for Mem0Adapter."""

    def test_mem0_adapter_add_memory_item(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that Mem0Adapter correctly adds memory items and returns the ID.

        This test verifies that:
        1. The adapter properly calls the underlying mem0 client
        2. The correct arguments are passed to the client
        3. The response ID is returned correctly
        """
        # Arrange - Mock the mem0 client
        mock_mem0_client = Mock()
        mock_response_id = str(uuid4())
        mock_mem0_client.add.return_value = {"id": mock_response_id}

        # Mock the mem0 module and its Mem0 class
        mock_mem0_class = Mock(return_value=mock_mem0_client)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)

        # Sample test data
        test_user_id = "test-user-123"
        test_text_content = "This is a sample memory item for testing"
        test_metadata = {
            "source": "test",
            "category": "sample",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        # Act - Create adapter and call add method
        adapter = Mem0Adapter()
        result_id = adapter.add(
            user_id=test_user_id,
            text_content=test_text_content,
            metadata=test_metadata,
        )

        # Assert - Verify the mock was called correctly
        mock_mem0_client.add.assert_called_once_with(
            messages=[{"role": "user", "content": test_text_content}],
            user_id=test_user_id,
            metadata=test_metadata,
        )

        # Assert - Verify the correct ID is returned
        assert result_id == mock_response_id

    def test_mem0_adapter_add_memory_item_with_minimal_data(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Mem0Adapter add method with minimal required data."""
        # Arrange
        mock_mem0_client = Mock()
        mock_response_id = str(uuid4())
        mock_mem0_client.add.return_value = {"id": mock_response_id}

        mock_mem0_class = Mock(return_value=mock_mem0_client)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)

        test_user_id = "minimal-user"
        test_text_content = "Minimal memory"

        # Act
        adapter = Mem0Adapter()
        result_id = adapter.add(user_id=test_user_id, text_content=test_text_content)

        # Assert
        mock_mem0_client.add.assert_called_once_with(
            messages=[{"role": "user", "content": test_text_content}],
            user_id=test_user_id,
            metadata=None,
        )
        assert result_id == mock_response_id

    def test_mem0_adapter_handles_client_initialization(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that the adapter properly initializes the mem0 client."""
        # Arrange
        mock_mem0_client = Mock()
        mock_mem0_class = Mock(return_value=mock_mem0_client)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)

        # Act
        adapter = Mem0Adapter()

        # Assert
        mock_mem0_class.assert_called_once()
        assert adapter._client is mock_mem0_client

    def test_mem0_adapter_search_memory_items(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that Mem0Adapter correctly searches memory items and returns results.

        This test verifies that:
        1. The adapter properly calls the underlying mem0 client search method
        2. The correct search arguments are passed to the client
        3. The search results are returned correctly
        """
        # Arrange - Mock the mem0 client
        mock_mem0_client = Mock()

        # Sample search results that mem0 would return
        mock_search_results = [
            {
                "id": str(uuid4()),
                "memory": "User likes coffee in the morning",
                "score": 0.95,
                "metadata": {"source": "chat", "timestamp": "2024-01-01T08:00:00Z"},
            },
            {
                "id": str(uuid4()),
                "memory": "User prefers tea in the afternoon",
                "score": 0.87,
                "metadata": {"source": "chat", "timestamp": "2024-01-01T14:00:00Z"},
            },
        ]
        mock_mem0_client.search.return_value = mock_search_results

        # Mock the mem0 module and its Mem0 class
        mock_mem0_class = Mock(return_value=mock_mem0_client)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)

        # Sample search parameters
        test_user_id = "search-user-456"
        test_search_text = "coffee preferences"
        test_limit = 10

        # Act - Create adapter and call search method
        adapter = Mem0Adapter()
        search_results = adapter.search(
            user_id=test_user_id, query=test_search_text, limit=test_limit
        )

        # Assert - Verify the mock was called correctly
        mock_mem0_client.search.assert_called_once_with(
            query=test_search_text, user_id=test_user_id, limit=test_limit
        )

        # Assert - Verify the correct results are returned
        assert search_results == mock_search_results
        assert len(search_results) == 2
        assert all("id" in result for result in search_results)
        assert all("memory" in result for result in search_results)

    def test_mem0_adapter_search_memory_items_with_minimal_params(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Mem0Adapter search method with minimal required parameters."""
        # Arrange
        mock_mem0_client = Mock()
        mock_search_results: list[dict[str, Any]] = []
        mock_mem0_client.search.return_value = mock_search_results

        mock_mem0_class = Mock(return_value=mock_mem0_client)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)

        test_user_id = "minimal-search-user"
        test_query = "simple search"

        # Act
        adapter = Mem0Adapter()
        search_results = adapter.search(user_id=test_user_id, query=test_query)

        # Assert
        mock_mem0_client.search.assert_called_once_with(
            query=test_query, user_id=test_user_id, limit=None
        )
        assert search_results == mock_search_results

    def test_mem0_adapter_search_memory_items_empty_results(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test Mem0Adapter search method when no results are found."""
        # Arrange
        mock_mem0_client = Mock()
        mock_mem0_client.search.return_value = []

        mock_mem0_class = Mock(return_value=mock_mem0_client)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)

        # Act
        adapter = Mem0Adapter()
        search_results = adapter.search(
            user_id="no-results-user", query="nonexistent query"
        )

        # Assert
        assert search_results == []
        assert len(search_results) == 0

    def test_mem0_adapter_get_memory_item(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that Mem0Adapter can retrieve a specific memory item."""
        # Arrange
        mock_mem0_client = Mock()
        test_memory_id = str(uuid4())
        mock_memory_item = {
            "id": test_memory_id,
            "memory": "Test memory content",
            "metadata": {"source": "test"},
        }
        mock_mem0_client.get.return_value = mock_memory_item

        mock_mem0_class = Mock(return_value=mock_mem0_client)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)

        # Act
        adapter = Mem0Adapter()
        result = adapter.get(test_memory_id)

        # Assert
        mock_mem0_client.get.assert_called_once_with(test_memory_id)
        assert result == mock_memory_item

    def test_mem0_adapter_get_memory_item_not_found(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that Mem0Adapter handles cases where memory item is not found."""
        # Arrange
        mock_mem0_client = Mock()
        mock_mem0_client.get.side_effect = Exception("Not found")

        mock_mem0_class = Mock(return_value=mock_mem0_client)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)

        # Act
        adapter = Mem0Adapter()
        result = adapter.get("nonexistent-id")

        # Assert
        assert result is None

    def test_mem0_adapter_delete_memory_item(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that Mem0Adapter can delete a memory item."""
        # Arrange
        mock_mem0_client = Mock()
        test_memory_id = str(uuid4())

        mock_mem0_class = Mock(return_value=mock_mem0_client)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)

        # Act
        adapter = Mem0Adapter()
        result = adapter.delete(test_memory_id)

        # Assert
        mock_mem0_client.delete.assert_called_once_with(test_memory_id)
        assert result is True

    def test_mem0_adapter_delete_memory_item_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that Mem0Adapter handles deletion failures gracefully."""
        # Arrange
        mock_mem0_client = Mock()
        mock_mem0_client.delete.side_effect = Exception("Delete failed")

        mock_mem0_class = Mock(return_value=mock_mem0_client)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)

        # Act
        adapter = Mem0Adapter()
        result = adapter.delete("some-id")

        # Assert
        assert result is False
