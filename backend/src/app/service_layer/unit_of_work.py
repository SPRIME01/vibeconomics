import abc
from typing import Any, Type

# Forward declare repository types if they are abstract, or use Any for now
# from app.adapters.repositories import AbstractSomeRepository # Example

class AbstractUnitOfWork(abc.ABC):
    """
    An abstract base class for implementing the Unit of Work pattern.
    It manages transactions and coordinates changes across repositories.
    """
    # repositories: Dict[str, Any] # Store instantiated repositories

    def __enter__(self) -> "AbstractUnitOfWork":
        """
        Allows the Unit of Work to be used as a context manager.
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, traceback: Any) -> None:
        """
        Handles exiting the context. Rolls back on exception, otherwise commits.

        Args:
            exc_type: The type of the exception, if any.
            exc_val: The exception instance, if any.
            traceback: The traceback object, if any.
        """
        if exc_type:
            self.rollback()
        else:
            self.commit()

    @abc.abstractmethod
    def commit(self) -> None:
        """
        Commits all changes made within the unit of work to the underlying data store.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self) -> None:
        """
        Rolls back all changes made within the unit of work, reverting to the previous state.
        """
        raise NotImplementedError

    # Example of how repositories might be accessed if managed by UoW
    # @property
    # @abc.abstractmethod
    # def some_repository(self) -> AbstractSomeRepository:
    #     """
    #     Provides access to a specific repository.
    #     """
    #     raise NotImplementedError
