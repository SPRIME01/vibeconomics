from collections.abc import Callable  # Added Callable
from typing import Annotated, Any

from fastapi import Depends

from app.adapters.message_bus_inmemory import InMemoryMessageBus
from app.adapters.uow_sqlmodel import SqlModelUnitOfWork
from app.core.base_aggregate import DomainEvent  # For MessageBusDep hint
from app.service_layer.message_bus import (
    AbstractMessageBus,  # Removed EventT as it's not used here generically
)
from app.service_layer.unit_of_work import AbstractUnitOfWork


# Placeholder for database session factory
def get_db_session_factory() -> Callable[
    [], Any
]:  # Return type is a callable that returns a session-like Any
    """
    Provides a factory for database sessions.

    In a real application, this would be configured to connect to a database
    (e.g., using SQLAlchemy sessionmaker or SQLModel Session with an engine).
    For this DI setup, it returns a factory for a dummy session.
    """

    class DummySession:
        """A dummy session class for DI testing without a real database."""

        def commit(self) -> None:
            """Simulates committing a transaction."""
            pass

        def rollback(self) -> None:
            """Simulates rolling back a transaction."""
            pass

        def close(self) -> None:
            """Simulates closing a session."""
            pass

        def __enter__(self) -> "DummySession":
            """Allows use as a context manager."""
            return self

        def __exit__(self, *args: Any) -> None:
            """Handles exiting the context."""
            pass

    def dummy_session_factory() -> DummySession:
        """Creates and returns a new DummySession instance."""
        return DummySession()

    return dummy_session_factory


# Global instance of message bus
# For simplicity, instantiated directly. In a larger app, manage via app state or a DI container.
message_bus_instance: AbstractMessageBus[DomainEvent] = InMemoryMessageBus[
    DomainEvent
]()


def get_uow(
    session_factory: Annotated[Callable[[], Any], Depends(get_db_session_factory)],
) -> AbstractUnitOfWork:
    """
    FastAPI dependency injector for Unit of Work.

    Args:
        session_factory: A callable that provides a database session.
                         Injected by FastAPI via `get_db_session_factory`.

    Returns:
        An instance of SqlModelUnitOfWork.
    """
    return SqlModelUnitOfWork(session_factory=session_factory)


def get_message_bus() -> AbstractMessageBus[DomainEvent]:  # Hinted with DomainEvent
    """
    FastAPI dependency injector for Message Bus.

    Returns:
        The globally available message_bus_instance.
    """
    return message_bus_instance


# Type Aliases for FastAPI dependencies
UoWDep = Annotated[AbstractUnitOfWork, Depends(get_uow)]
MessageBusDep = Annotated[AbstractMessageBus[DomainEvent], Depends(get_message_bus)]
