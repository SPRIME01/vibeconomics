from typing import List, TypeVar, Generic, NewType
from pydantic import BaseModel, Field
import abc
import uuid

EventT = TypeVar('EventT') # Generic type for events
AggregateId = NewType('AggregateId', uuid.UUID)

class DomainEvent(BaseModel):
    """
    Represents a domain event.

    Attributes:
        event_id: The unique identifier for the event.
    """
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    # timestamp: datetime = Field(default_factory=datetime.utcnow) # Consider adding later

class AggregateRoot(Generic[EventT], abc.ABC):
    """
    Base class for aggregate roots in the domain model.

    Attributes:
        id: The unique identifier of the aggregate.
        version: The version number of the aggregate for optimistic concurrency control.
    """
    id: AggregateId
    version: int = Field(default=0) # For optimistic concurrency control

    def __init__(self, id: AggregateId) -> None:
        """
        Initializes the AggregateRoot.

        Args:
            id: The unique identifier of the aggregate.
        """
        self.id = id
        self._events: List[EventT] = []

    @property
    def events(self) -> List[EventT]:
        """
        Returns the list of domain events recorded by this aggregate.
        """
        return self._events

    def add_event(self, event: EventT) -> None:
        """
        Adds a domain event to the aggregate.

        Args:
            event: The domain event to add.
        """
        self._events.append(event)
        # Optionally, immediately publish events or handle them here if not using a separate bus

    def clear_events(self) -> None:
        """
        Clears all recorded domain events from the aggregate.
        """
        self._events = []

    # Pydantic compatibility if needed for serialization
    # class Config:
    #     arbitrary_types_allowed = True
