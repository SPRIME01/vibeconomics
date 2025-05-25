"""Unit of Work pattern implementation for managing transaction boundaries."""

from types import TracebackType
from typing import Any, Protocol, runtime_checkable


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
