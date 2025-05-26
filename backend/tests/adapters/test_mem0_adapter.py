"""Tests for Mem0 adapter implementation."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.adapters.mem0_adapter import Mem0Adapter, Mem0Memory


class TestMem0Adapter:
    """Test suite for Mem0Adapter."""

    @pytest.fixture
    def mock_memory_client(self, monkeypatch: pytest.MonkeyPatch) -> Mock:
        """Fixture to mock the MemoryClient."""
        mock_client = Mock()
        mock_mem0_class = Mock(return_value=mock_client)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)
        return mock_client

    def test_mem0_adapter_initialization_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test adapter initialization failure."""
        mock_mem0_class = Mock(side_effect=RuntimeError("Init failed"))
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)
        with pytest.raises(
            RuntimeError, match="Failed to initialize Mem0Client: Init failed"
        ):
            Mem0Adapter()

    # --- Add Method Tests ---
    def test_mem0_adapter_add_memory_item_success(
        self, mock_memory_client: Mock
    ) -> None:
        """Test successful addition of a memory item."""
        mock_response_id = str(uuid4())
        mock_memory_client.add.return_value = {"id": mock_response_id}

        adapter = Mem0Adapter()
        result_id = adapter.add(
            user_id="test-user",
            text_content="Test content",
            metadata={"source": "test"},
        )

        mock_memory_client.add.assert_called_once()
        assert result_id == mock_response_id

    def test_mem0_adapter_add_memory_item_client_error(
        self, mock_memory_client: Mock
    ) -> None:
        """Test add method when mem0 client raises an error."""
        mock_memory_client.add.side_effect = Exception("Client add error")

        adapter = Mem0Adapter()
        result_id = adapter.add(user_id="test-user", text_content="Test content")

        assert result_id is None

    def test_mem0_adapter_add_memory_item_malformed_response(
        self, mock_memory_client: Mock
    ) -> None:
        """Test add method when mem0 client returns a malformed response."""
        mock_memory_client.add.return_value = {
            "wrong_key": "some_value"
        }  # Missing 'id'

        adapter = Mem0Adapter()
        result_id = adapter.add(user_id="test-user", text_content="Test content")

        assert result_id is None

    # --- Search Method Tests ---
    def test_mem0_adapter_search_memory_items_success(
        self, mock_memory_client: Mock
    ) -> None:
        """Test successful search of memory items."""
        raw_item_1 = {
            "id": str(uuid4()),
            "memory": "Memory 1",
            "score": 0.9,
            "metadata": {"cat": "A"},
        }
        raw_item_2 = {"id": str(uuid4()), "memory": "Memory 2", "score": 0.8}
        mock_memory_client.search.return_value = [raw_item_1, raw_item_2]

        adapter = Mem0Adapter()
        results = adapter.search(user_id="test-user", query="test query")

        assert len(results) == 2
        assert isinstance(results[0], Mem0Memory)
        assert results[0].id == raw_item_1["id"]
        assert results[0].memory == raw_item_1["memory"]
        assert results[1].id == raw_item_2["id"]
        mock_memory_client.search.assert_called_once()

    def test_mem0_adapter_search_memory_items_client_error(
        self, mock_memory_client: Mock
    ) -> None:
        """Test search method when mem0 client raises an error."""
        mock_memory_client.search.side_effect = Exception("Client search error")

        adapter = Mem0Adapter()
        results = adapter.search(user_id="test-user", query="test query")

        assert results == []

    def test_mem0_adapter_search_memory_items_empty_results(
        self, mock_memory_client: Mock
    ) -> None:
        """Test search method when mem0 client returns an empty list."""
        mock_memory_client.search.return_value = []

        adapter = Mem0Adapter()
        results = adapter.search(user_id="test-user", query="test query")

        assert results == []

    def test_mem0_adapter_search_malformed_item_in_results(
        self, mock_memory_client: Mock
    ) -> None:
        """Test search method with one malformed item in results."""
        raw_item_valid = {"id": str(uuid4()), "memory": "Valid Memory", "score": 0.9}
        raw_item_invalid = {
            "id_missing": str(uuid4()),
            "memory": "Invalid Memory",
        }  # 'id' is missing
        mock_memory_client.search.return_value = [raw_item_valid, raw_item_invalid]

        adapter = Mem0Adapter()
        results = adapter.search(user_id="test-user", query="test query")

        assert len(results) == 1
        assert results[0].id == raw_item_valid["id"]

    # --- Get Method Tests ---
    def test_mem0_adapter_get_memory_item_success(
        self, mock_memory_client: Mock
    ) -> None:
        """Test successful retrieval of a memory item."""
        memory_id = str(uuid4())
        raw_item = {
            "id": memory_id,
            "memory": "Specific Memory",
            "metadata": {"detail": "X"},
        }
        mock_memory_client.get.return_value = raw_item

        adapter = Mem0Adapter()
        result = adapter.get(memory_id)

        assert isinstance(result, Mem0Memory)
        assert result.id == memory_id
        assert result.memory == "Specific Memory"
        mock_memory_client.get.assert_called_once_with(memory_id)

    def test_mem0_adapter_get_memory_item_client_error(
        self, mock_memory_client: Mock
    ) -> None:
        """Test get method when mem0 client raises an error."""
        mock_memory_client.get.side_effect = Exception("Client get error")

        adapter = Mem0Adapter()
        result = adapter.get("some-id")

        assert result is None

    def test_mem0_adapter_get_memory_item_not_found_returns_none(
        self, mock_memory_client: Mock
    ) -> None:
        """Test get method when mem0 client returns None (or equivalent for not found)."""
        # Some clients might raise specific "NotFound" errors, others might return None/empty.
        # Assuming client returns something that results in None after adapter logic.
        # If client raises an exception for "not found", test_mem0_adapter_get_memory_item_client_error covers it.
        # If client returns None or empty dict:
        mock_memory_client.get.return_value = None

        adapter = Mem0Adapter()
        result = adapter.get("nonexistent-id")
        assert result is None

        mock_memory_client.get.return_value = {}  # Malformed, missing 'id' and 'memory'
        result_malformed = adapter.get("malformed-id")
        assert result_malformed is None

    def test_mem0_adapter_get_memory_item_malformed_response(
        self, mock_memory_client: Mock
    ) -> None:
        """Test get method when mem0 client returns a malformed response."""
        mock_memory_client.get.return_value = {
            "wrong_key": "some_value"
        }  # Missing 'id' and 'memory'

        adapter = Mem0Adapter()
        result = adapter.get("some-id")

        assert result is None

    # --- Update Method Tests ---
    def test_mem0_adapter_update_memory_item_success(
        self, mock_memory_client: Mock
    ) -> None:
        """Test successful update of a memory item."""
        memory_id = str(uuid4())
        update_data = {"memory": "Updated Content", "metadata": {"status": "revised"}}
        # Assume client's update returns the full updated object
        raw_updated_item = {
            "id": memory_id,
            "memory": "Updated Content",
            "metadata": {"status": "revised"},
        }
        mock_memory_client.update.return_value = raw_updated_item

        adapter = Mem0Adapter()
        result = adapter.update(memory_id, update_data)

        assert isinstance(result, Mem0Memory)
        assert result.id == memory_id
        assert result.memory == "Updated Content"
        assert result.metadata == {"status": "revised"}
        mock_memory_client.update.assert_called_once_with(memory_id, update_data)

    def test_mem0_adapter_update_memory_item_client_error(
        self, mock_memory_client: Mock
    ) -> None:
        """Test update method when mem0 client raises an error."""
        memory_id = str(uuid4())
        update_data = {"memory": "Updated Content"}
        mock_memory_client.update.side_effect = Exception("Client update error")

        adapter = Mem0Adapter()
        result = adapter.update(memory_id, update_data)

        assert result is None

    def test_mem0_adapter_update_memory_item_malformed_response(
        self, mock_memory_client: Mock
    ) -> None:
        """Test update method when mem0 client returns a malformed response."""
        memory_id = str(uuid4())
        update_data = {"memory": "Updated Content"}
        mock_memory_client.update.return_value = {
            "wrong_key": "some_value"
        }  # Missing 'id' and 'memory'

        adapter = Mem0Adapter()
        result = adapter.update(memory_id, update_data)

        assert result is None

    def test_mem0_adapter_update_memory_item_client_returns_none(
        self, mock_memory_client: Mock
    ) -> None:
        """Test update method when mem0 client returns None."""
        memory_id = str(uuid4())
        update_data = {"memory": "Updated Content"}
        mock_memory_client.update.return_value = None

        adapter = Mem0Adapter()
        result = adapter.update(memory_id, update_data)

        assert result is None

    # --- Delete Method Tests ---
    def test_mem0_adapter_delete_memory_item_success(
        self, mock_memory_client: Mock
    ) -> None:
        """Test successful deletion of a memory item."""
        memory_id = str(uuid4())
        # mock_memory_client.delete doesn't need a return_value if it's just successful execution

        adapter = Mem0Adapter()
        result = adapter.delete(memory_id)

        assert result is True
        mock_memory_client.delete.assert_called_once_with(memory_id)

    def test_mem0_adapter_delete_memory_item_client_error(
        self, mock_memory_client: Mock
    ) -> None:
        """Test delete method when mem0 client raises an error."""
        mock_memory_client.delete.side_effect = Exception("Client delete error")

        adapter = Mem0Adapter()
        result = adapter.delete("some-id")

        assert result is False

    # --- Original Tests (adapted for new signatures/mocks if needed) ---
    # The original tests were mostly covered by the new granular tests.
    # I'll ensure the core scenarios from them are present.

    def test_mem0_adapter_handles_client_initialization(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that the adapter properly initializes the mem0 client."""
        mock_mem0_client_instance = Mock()
        mock_mem0_class = Mock(return_value=mock_mem0_client_instance)
        monkeypatch.setattr("app.adapters.mem0_adapter.MemoryClient", mock_mem0_class)

        adapter = Mem0Adapter()

        mock_mem0_class.assert_called_once()
        assert adapter._client is mock_mem0_client_instance
