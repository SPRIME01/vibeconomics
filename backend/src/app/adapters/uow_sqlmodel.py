from typing import Any, Dict, Callable # Added Callable back for clarity, though prompt says Any for factory
from sqlmodel import Session # Assuming SQLModel is the chosen ORM
# from sqlalchemy.orm import sessionmaker # If using raw SQLAlchemy
# from app.core.config import settings # If you have a db connection string here

from app.service_layer.unit_of_work import AbstractUnitOfWork
# Import repository interfaces if they exist, e.g.:
# from app.domain.ports.repositories import AbstractProductRepository
# from .repositories_sqlmodel import ProductRepository # Concrete repo

# Placeholder for DB session factory - replace with your actual setup
# engine = create_engine(settings.DATABASE_URL) # Example
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class SqlModelUnitOfWork(AbstractUnitOfWork):
    """A Unit of Work implementation using SQLModel and a SQLAlchemy session."""
    # session: Session # This will be the SQLModel session
    # repositories: Dict[str, Any] # To hold instantiated repositories

    def __init__(self, session_factory: Any # Prompt: Any, comment: Callable[[], Session]
                 # Pass repository factories or types if UoW creates them
                ):
        """
        Initializes the SQLModelUnitOfWork.

        Args:
            session_factory: A callable that returns a new SQLModel session.
        """
        self.session_factory: Any = session_factory # Using Any as per prompt for the type hint
        self.session: Session # Will be set in __enter__, type hint here for clarity
        # self.products = ProductRepository(self.session) # Example instantiation

    def __enter__(self) -> "SqlModelUnitOfWork":
        """Starts a new transaction and session."""
        self.session = self.session_factory()
        # self.products = ProductRepository(self.session) # Re-init with new session
        return super().__enter__()

    def __exit__(self, exc_type: Any, exc_val: Any, traceback: Any) -> None:
        """Handles session commit or rollback and closes the session."""
        super().__exit__(exc_type, exc_val, traceback)
        if self.session: # Ensure session was created
            self.session.close()

    def commit(self) -> None:
        """Commits the current session's transaction."""
        if self.session: # Ensure session was created
            self.session.commit()

    def rollback(self) -> None:
        """Rolls back the current session's transaction."""
        if self.session: # Ensure session was created
            self.session.rollback()

    # Example of a repository property:
    # @property
    # def products(self) -> AbstractProductRepository:
    #     return self._products # Assuming _products is initialized with the session
