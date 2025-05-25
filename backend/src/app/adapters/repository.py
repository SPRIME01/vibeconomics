from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from sqlmodel import Session, SQLModel

# Generic TypeVariables for Repository
T = TypeVar("T", bound=SQLModel)  # Type of the entity
U = TypeVar("U", bound=SQLModel)  # Type of the create schema
V = TypeVar("V", bound=SQLModel)  # Type of the update schema


class AbstractRepository(ABC, Generic[T, U, V]):
    """Abstract Repository for CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    @abstractmethod
    def get(self, id: UUID) -> T | None:
        raise NotImplementedError

    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        raise NotImplementedError

    @abstractmethod
    def create(self, obj_in: U) -> T:
        raise NotImplementedError

    @abstractmethod
    def update(self, db_obj: T, obj_in: V) -> T:
        raise NotImplementedError

    @abstractmethod
    def remove(self, id: UUID) -> T | None:
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository[T, U, V]):
    """SQLAlchemy specific Repository implementation."""

    def __init__(self, session: Session, model: type[T]):
        super().__init__(session)
        self.model = model

    def get(self, id: UUID) -> T | None:
        return self.session.get(self.model, id)

    def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        return list(self.session.query(self.model).offset(skip).limit(limit).all())

    def create(self, obj_in: U) -> T:
        db_obj = self.model.model_validate(obj_in)  # SQLModel v0.0.12+
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def update(self, db_obj: T, obj_in: V) -> T:
        obj_data = obj_in.model_dump(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def remove(self, id: UUID) -> T | None:
        obj = self.session.get(self.model, id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
        return obj


# Example of a specific repository (can be defined here or in a dedicated user_repository.py)
# from app.adapters.orm import User
# from app.entrypoints.schemas import UserCreate, UserUpdate

# class UserRepository(SQLAlchemyRepository[User, UserCreate, UserUpdate]):
#     def __init__(self, session: Session):
#         super().__init__(session, User)

#     # Add user-specific methods here if any, e.g.:
#     def get_by_email(self, email: str) -> User | None:
#         return self.session.query(self.model).filter(self.model.email == email).first()
