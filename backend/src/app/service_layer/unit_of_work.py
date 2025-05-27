"""Unit of Work pattern implementation for managing transaction boundaries."""

from types import TracebackType
from typing import Any, Protocol, runtime_checkable

from app.adapters.conversation_repository_inmemory import InMemoryConversationRepository


@runtime_checkable
class AbstractUnitOfWork(Protocol):
    """Protocol for Unit of Work pattern managing transactional consistency.

    The Unit of Work pattern coordinates the writing out of changes and
    resolves concurrency problems. It maintains a list of objects affected
    by a business transaction and coordinates writing out changes.
    """

    repositories: dict[str, Any]

    async def __aenter__(self) -> "AbstractUnitOfWork":
        """Start a new transaction and return self.

        This method is called when entering an async context manager.
        It should initialize any necessary resources like database sessions.

        Returns:
            Self to enable context manager protocol.
        """
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Clean up resources and handle transaction completion.

        If an exception occurred during the context, this should rollback
        the transaction. Otherwise, the transaction should have been
        committed explicitly via commit().

        Args:
            exc_type: The exception type if an exception was raised.
            exc_val: The exception instance if an exception was raised.
            exc_tb: The traceback if an exception was raised.
        """
        ...

    async def commit(self) -> None:
        """Commit the current transaction.

        This should persist all changes made during the unit of work
        and publish any domain events that were collected.

        Raises:
            CommitError: If the commit operation fails.
        """
        ...

    async def rollback(self) -> None:
        """Roll back the current transaction.

        This should discard all changes made during the unit of work
        and clean up any resources.

        Raises:
            RollbackError: If the rollback operation fails.
        """
        ...

    async def collect_new_events(self) -> list[Any]:
        """Collect domain events from aggregates for publishing.

        This method should traverse all tracked aggregates and collect
        any new domain events that need to be published.

        Returns:
            List of domain events to be published.
        """
        ...


class FakeUnitOfWork(AbstractUnitOfWork):
    """
    A fake Unit of Work for testing purposes.
    It uses an in-memory conversation repository and implements required protocol methods.
    """

    def __init__(self):
        self.conversations = InMemoryConversationRepository()
        self.repositories = {"conversations": self.conversations}
        self.committed = False
        self.rolled_back = False

    async def collect_new_events(self) -> list[Any]:
        """Collect domain events from aggregates for publishing."""
        return []

    async def __aenter__(self) -> "FakeUnitOfWork":
        self.committed = False
        self.rolled_back = False
        # Re-initialize for better test isolation
        self.conversations = InMemoryConversationRepository()
        self.repositories = {"conversations": self.conversations}
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc:
            await self.rollback()
        # If no exception, commit() should have been called explicitly by the service.
        # If not committed, the UoW pattern implies changes are discarded (rolled back).
        # Our rollback flag is set by explicit calls, __aexit__ handles implicit rollback on error.

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True
