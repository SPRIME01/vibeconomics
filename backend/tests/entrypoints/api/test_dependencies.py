from collections.abc import Callable  # Added for mock_session_factory type hint
from typing import Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.entrypoints.api.dependencies import (
    get_db_session_factory,
    get_message_bus,
)

# Assuming main.py is in backend/src/app/entrypoints/api/main.py
# Adjust import if your app instance is elsewhere or named differently.
from app.entrypoints.api.main import app
from app.service_layer.message_bus import AbstractMessageBus  # Removed EventT

client = TestClient(app)


def test_uow_dependency_injection() -> None:
    """Test that the UoW dependency is correctly injected."""
    # Mock the session factory to avoid actual DB interaction
    mock_session_factory = MagicMock(
        spec=Callable[[], Any]
    )  # Mocking a factory that returns a session
    mock_session = MagicMock()
    # Configure the factory's return_value to be another mock (the session itself)
    # This way, when session_factory() is called, it returns mock_session
    mock_session_factory.return_value = mock_session

    # Override the dependency for this test
    app.dependency_overrides[get_db_session_factory] = lambda: mock_session_factory

    response = client.post("/test-di-uow")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["is_uow_instance"] is True

    # Check if the factory was called (FastAPI calls get_db_session_factory, then get_uow calls the factory)
    # get_db_session_factory returns mock_session_factory.
    # get_uow receives mock_session_factory and calls it: uow = SqlModelUnitOfWork(session_factory=mock_session_factory)
    # Inside SqlModelUnitOfWork.__enter__, self.session = self.session_factory() is called.
    # The factory mock_session_factory (which is self.session_factory in UoW)
    # is only called if the UoW is used as a context manager in the endpoint.
    # The current endpoint /test-di-uow does not use it that way.
    # So, we cannot assert mock_session_factory.called here.
    # The main test is that an instance of AbstractUnitOfWork was successfully injected.

    # Clean up dependency override
    app.dependency_overrides = {}


def test_message_bus_dependency_injection() -> None:
    """Test that the MessageBus dependency is correctly injected."""

    # Create a mock that IS an AbstractMessageBus for isinstance checks in the endpoint
    class MockMessageBus(
        AbstractMessageBus[Any]
    ):  # Use Any to match MessageBusDep type hint
        def publish(self, event: Any) -> None:
            pass  # pragma: no cover

        def subscribe(
            self, event_type: type[Any], handler: Callable[[Any], None]
        ) -> None:
            pass  # pragma: no cover

    mock_bus_instance = MockMessageBus()
    app.dependency_overrides[get_message_bus] = lambda: mock_bus_instance

    response = client.post("/test-di-message-bus")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["is_bus_instance"] is True

    # Clean up dependency override
    app.dependency_overrides = {}


def test_concrete_uow_dependency_injection() -> None:
    """Test direct dependency injection of UoW."""
    mock_db_session_factory = MagicMock(
        spec=Callable[[], Any]
    )  # This is the factory for sessions
    # mock_session = MagicMock() # Not strictly needed if we don't check calls on session itself
    # mock_db_session_factory.return_value = mock_session

    app.dependency_overrides[get_db_session_factory] = lambda: mock_db_session_factory

    response = client.post("/test-di-concrete-uow")
    assert response.status_code == 200
    assert response.json()["is_uow_instance"] is True
    # Similar to test_uow_dependency_injection, mock_db_session_factory (which becomes
    # session_factory in get_uow, then passed to SqlModelUnitOfWork)
    # will not be called unless the UoW is used as a context manager in the endpoint.

    app.dependency_overrides = {}
