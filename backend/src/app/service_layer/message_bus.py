"""Message bus implementation for event handling and dispatching."""

from typing import Protocol, runtime_checkable

from app.core.base_aggregate import DomainEvent


@runtime_checkable
class AbstractMessageBus(Protocol):
    """Protocol for message bus responsible for handling and dispatching events."""

    async def publish(self, event: DomainEvent) -> None:
        """
        Publishes an event to all subscribed handlers.

        Args:
            event: The domain event to publish.
        """
        ...
