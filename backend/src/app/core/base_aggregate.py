import uuid
from typing import NewType, TypeVar

from pydantic import BaseModel, Field, PrivateAttr

EventT = TypeVar("EventT")  # Generic type for events
AggregateId = NewType("AggregateId", uuid.UUID)


class DomainEvent(BaseModel):
    """
    Represents a domain event.

    Attributes:
        event_id: The unique identifier for the event.
    """

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    # timestamp: datetime = Field(default_factory=datetime.utcnow) # Consider adding later


class AggregateRoot(BaseModel):
    """
    Base class for aggregate roots in the domain model.

    Provides event management functionality and ensures each aggregate
    has a unique identifier.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    _events: list[DomainEvent] = PrivateAttr(default_factory=list[DomainEvent])

    def add_event(self, event: DomainEvent) -> None:
        """
        Add a domain event to the aggregate's event list.

        Args:
            event: The domain event to add
        """
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """
        Return all stored events and clear the internal list.

        Returns:
            List of domain events that were stored
        """
        events = self._events.copy()
        self._events.clear()
        return events

    class Config:
        """Pydantic configuration to allow arbitrary field types."""

        arbitrary_types_allowed = True
