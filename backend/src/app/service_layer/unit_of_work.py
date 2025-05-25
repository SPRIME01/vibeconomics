"""Unit of Work pattern implementation for managing transaction boundaries."""

from types import TracebackType
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AbstractUnitOfWork(Protocol):
    """Protocol for Unit of Work pattern managing transactional consistency."""

    repositories: dict[str, Any]

    async def __aenter__(self) -> "AbstractUnitOfWork":
        """Start a new transaction and return self."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Roll back transaction if not committed."""
        ...

    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        ...
