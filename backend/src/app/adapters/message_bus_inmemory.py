import asyncio
from collections import defaultdict
from collections.abc import Callable

from app.core.base_aggregate import DomainEvent


class InMemoryMessageBus:
    """In-memory implementation of message bus for testing and simple deployments."""

    def __init__(self) -> None:
        self.subscriptions: dict[
            type[DomainEvent], list[Callable[[DomainEvent], None]]
        ] = defaultdict(list)
        self.published_events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        """
        Publishes an event to all subscribed handlers.

        Args:
            event: The domain event to publish.
        """
        self.published_events.append(event)

        # Call all registered handlers for this event type
        event_type = type(event)
        for handler in self.subscriptions[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                # Log error but don't stop processing other handlers
                print(f"Error in event handler: {e}")

    def subscribe(
        self, event_type: type[DomainEvent], handler: Callable[[DomainEvent], None]
    ) -> None:
        """
        Subscribes a handler to a specific event type.

        Args:
            event_type: The type of the event to subscribe to.
            handler: The callable function that will handle the event.
        """
        self.subscriptions[event_type].append(handler)

    def clear_subscriptions(self) -> None:
        """Clear all subscriptions - useful for testing."""
        self.subscriptions.clear()

    def clear_published_events(self) -> None:
        """Clear published events history - useful for testing."""
        self.published_events.clear()
