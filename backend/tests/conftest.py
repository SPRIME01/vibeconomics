from unittest.mock import MagicMock

import pytest

from app.adapters.message_bus_inmemory import InMemoryMessageBus  # For testing
from app.core.base_aggregate import DomainEvent
from app.service_layer.unit_of_work import AbstractUnitOfWork


# Mock UoW for testing
class MockUnitOfWork(AbstractUnitOfWork):
    def __init__(self) -> None:
        self.committed: bool = False  # Explicitly typed
        self.rolled_back: bool = False  # Explicitly typed

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


@pytest.fixture
def mock_uow() -> MockUnitOfWork:  # Removed self
    return MockUnitOfWork()


# In-memory message bus fixture for testing event handling
@pytest.fixture
def in_memory_message_bus() -> InMemoryMessageBus[DomainEvent]:  # Removed self
    return InMemoryMessageBus[DomainEvent]()


# Example Domain Event for testing
class TestEvent(DomainEvent):
    data: str


# Mock command bus for testing command dispatch
@pytest.fixture
def mock_command_bus() -> MagicMock:  # Removed self
    return MagicMock()
