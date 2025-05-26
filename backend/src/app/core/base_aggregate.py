import uuid
from typing import Generic, NewType, TypeVar

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

EventT = TypeVar("EventT", bound="DomainEvent")  # Generic type for events
AggregateId = NewType("AggregateId", uuid.UUID)


class DomainEvent(BaseModel):
    """
    Represents a domain event.

    Domain events are immutable records of something significant that
    happened in the domain. They are used to communicate changes
    between bounded contexts and trigger side effects.

    Attributes:
        event_id: The unique identifier for the event.
    """

    model_config = ConfigDict(frozen=True)

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    # timestamp: datetime = Field(default_factory=datetime.utcnow) # Consider adding later


class AggregateRoot(BaseModel, Generic[EventT]):
    """
    Base class for aggregate roots in the domain model.

    An aggregate root is the only entry point for commands and queries
    to the aggregate. It ensures consistency boundaries and manages
    domain events that represent state changes.

    The aggregate root is responsible for:
    - Maintaining aggregate invariants
    - Coordinating changes across entities within the aggregate
    - Recording domain events when significant changes occur
    - Providing a consistent interface to the aggregate
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    _events: list[EventT] = PrivateAttr(default_factory=list[EventT])

    def add_event(self, event: EventT) -> None:
        """
        Add a domain event to the aggregate's event list.

        Domain events should be added when the aggregate's state changes
        in a way that other parts of the system need to know about.

        Args:
            event: The domain event to add
        """
        self._events.append(event)

    def pull_events(self) -> list[EventT]:
        """
        Return all stored events and clear the internal list.

        This method is typically called by the Unit of Work pattern
        to collect events for publishing after a successful transaction.

        Returns:
            List of domain events that were stored. The internal list
            is cleared after this call.
        """
        events = self._events.copy()
        self._events.clear()
        return events
