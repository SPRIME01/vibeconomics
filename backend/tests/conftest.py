from types import TracebackType  # Add TracebackType
from typing import Any  # Add Any
from unittest.mock import MagicMock

import pytest

from app.adapters.message_bus_inmemory import InMemoryMessageBus
from app.core.base_aggregate import DomainEvent
from app.service_layer.unit_of_work import AbstractUnitOfWork


# Mock UoW for testing
class MockUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self.repositories: dict[str, Any] = {}  # Add repositories attribute
        self.committed: bool = False
        self.rolled_back: bool = False

    async def __aenter__(self) -> "MockUnitOfWork":  # Make async
        self.committed = False
        self.rolled_back = False
        return self

    async def __aexit__(  # Make async
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if (
            exc_type is not None and not self.committed
        ):  # Rollback on exception if not committed
            await self.rollback()
        elif (
            not self.committed and not self.rolled_back
        ):  # Ensure rollback if not committed
            await self.rollback()

    async def commit(self) -> None:  # Make async
        self.committed = True

    async def rollback(self) -> None:  # Make async
        self.rolled_back = True


@pytest.fixture
def mock_uow() -> MockUnitOfWork:  # Removed self
    return MockUnitOfWork()


# In-memory message bus fixture for testing event handling
@pytest.fixture
def in_memory_message_bus() -> InMemoryMessageBus:  # Removed self and generic type
    """Provides an in-memory message bus for testing."""
    return InMemoryMessageBus()


# Example Domain Event for testing
class TestEvent(DomainEvent):
    data: str


# Mock command bus for testing command dispatch
@pytest.fixture
def mock_command_bus() -> MagicMock:  # Removed self
    return MagicMock()
