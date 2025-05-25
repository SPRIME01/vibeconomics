"""Message bus implementation for event handling and dispatching."""

from typing import Any, Protocol, runtime_checkable

from app.core.base_aggregate import DomainEvent


@runtime_checkable
class AbstractMessageBus(Protocol):
    """Protocol for message bus responsible for handling and dispatching events.

    The message bus serves as the central hub for all domain events and commands,
    ensuring loose coupling between different parts of the system.
    """

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered handlers.

        Args:
            event: The domain event to publish.

        Raises:
            PublishError: If the event cannot be published.
        """
        ...

    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """Publish multiple domain events in a batch.

        This method should handle publishing multiple events efficiently,
        potentially with better performance than individual publish calls.

        Args:
            events: List of domain events to publish.

        Raises:
            PublishError: If any event in the batch cannot be published.
        """
        ...

    def register_handler(self, event_type: type[DomainEvent], handler: Any) -> None:
        """Register an event handler for a specific event type.

        Args:
            event_type: The type of event to handle.
            handler: The handler function or callable.

        Raises:
            RegistrationError: If the handler cannot be registered.
        """
        ...
