from unittest.mock import Mock
import pytest
from typing import Any, Type, Protocol

# Import with type annotations to help static analysis
from app.service_layer.command_handlers.memory_handlers import StoreMemoryCommandHandler  # type: ignore
from app.domain.memory.commands import StoreMemoryCommand  # type: ignore
from app.domain.memory.events import MemoryStoredEvent  # type: ignore
from app.domain.memory.entities import Memory  # type: ignore
from app.infrastructure.memory.repository import AbstractMemoryRepository  # type: ignore
from app.infrastructure.core.unit_of_work import AbstractUnitOfWork  # type: ignore
from app.infrastructure.core.message_bus import AbstractMessageBus  # type: ignore


class TestStoreMemoryCommandHandler:
    """Test suite for StoreMemoryCommandHandler following DDD patterns."""

    @pytest.fixture
    def mock_memory_repository(self) -> Mock:
        """Mock memory repository following AbstractMemoryRepository interface."""
        repo = Mock(spec=AbstractMemoryRepository)
        return repo

    @pytest.fixture
    def mock_unit_of_work(self, mock_memory_repository: Mock) -> Mock:
        """Mock unit of work with memory repository."""
        uow = Mock(spec=AbstractUnitOfWork)
        uow.memories = mock_memory_repository
        uow.__enter__ = Mock(return_value=uow)
        uow.__exit__ = Mock(return_value=None)
        return uow

    @pytest.fixture
    def mock_message_bus(self) -> Mock:
        """Mock message bus for event publishing."""
        return Mock(spec=AbstractMessageBus)

    @pytest.fixture
    def handler(self, mock_unit_of_work: Mock, mock_message_bus: Mock) -> StoreMemoryCommandHandler:
        """Create handler instance with mocked dependencies."""
        return StoreMemoryCommandHandler(
            uow=mock_unit_of_work,
            message_bus=mock_message_bus
        )

    @pytest.fixture
    def store_memory_command(self) -> StoreMemoryCommand:
        """Create a sample store memory command."""
        return StoreMemoryCommand(
            user_id="user123",
            content="Test memory content",
            metadata={"source": "test"}
        )

    def test_handler_calls_repository_add_method(
        self,
        handler: StoreMemoryCommandHandler,
        store_memory_command: StoreMemoryCommand,
        mock_unit_of_work: Mock
    ) -> None:
        """Test that handler correctly calls repository's add method."""
        # Act
        result = handler.handle(store_memory_command)

        # Assert
        mock_unit_of_work.memories.add.assert_called_once()

        # Verify the Memory object passed to add has correct properties
        added_memory = mock_unit_of_work.memories.add.call_args[0][0]
        assert isinstance(added_memory, Memory)
        assert added_memory.user_id == store_memory_command.user_id
        assert added_memory.content == store_memory_command.content
        assert added_memory.metadata == store_memory_command.metadata

    def test_handler_calls_uow_commit(
        self,
        handler: StoreMemoryCommandHandler,
        store_memory_command: StoreMemoryCommand,
        mock_unit_of_work: Mock
    ) -> None:
        """Test that handler calls uow.commit()."""
        # Act
        handler.handle(store_memory_command)

        # Assert
        mock_unit_of_work.commit.assert_called_once()

    def test_handler_publishes_memory_stored_event(
        self,
        handler: StoreMemoryCommandHandler,
        store_memory_command: StoreMemoryCommand,
        mock_message_bus: Mock
    ) -> None:
        """Test that handler publishes MemoryStoredEvent."""
        # Act
        result = handler.handle(store_memory_command)

        # Assert
        mock_message_bus.publish.assert_called_once()

        # Verify the published event
        published_event = mock_message_bus.publish.call_args[0][0]
        assert isinstance(published_event, MemoryStoredEvent)
        assert published_event.user_id == store_memory_command.user_id
        assert published_event.content == store_memory_command.content
        assert published_event.metadata == store_memory_command.metadata
        assert published_event.memory_id == result

    def test_handler_returns_memory_id(
        self,
        handler: StoreMemoryCommandHandler,
        store_memory_command: StoreMemoryCommand
    ) -> None:
        """Test that handler returns the memory ID."""
        # Act
        result = handler.handle(store_memory_command)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0

    def test_handler_uses_uow_context_manager(
        self,
        handler: StoreMemoryCommandHandler,
        store_memory_command: StoreMemoryCommand,
        mock_unit_of_work: Mock
    ) -> None:
        """Test that handler properly uses UoW as context manager."""
        # Act
        handler.handle(store_memory_command)

        # Assert
        mock_unit_of_work.__enter__.assert_called_once()
        mock_unit_of_work.__exit__.assert_called_once()

    def test_handler_rollback_on_exception(
        self,
        mock_unit_of_work: Mock,
        mock_message_bus: Mock,
        store_memory_command: StoreMemoryCommand
    ) -> None:
        """Test that handler properly handles exceptions and rollback."""
        # Arrange
        mock_unit_of_work.memories.add.side_effect = Exception("Repository error")
        handler = StoreMemoryCommandHandler(
            uow=mock_unit_of_work,
            message_bus=mock_message_bus
        )

        # Act & Assert
        with pytest.raises(Exception, match="Repository error"):
            handler.handle(store_memory_command)

        # Verify rollback behavior through context manager
        mock_unit_of_work.__enter__.assert_called_once()
        mock_unit_of_work.__exit__.assert_called_once()

        # Commit should not be called on error
        mock_unit_of_work.commit.assert_not_called()

        # Event should not be published on error
        mock_message_bus.publish.assert_not_called()# from app.service_layer.command_handlers.memory_handlers import StoreMemoryCommandHandler
