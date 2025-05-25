import logging
from collections import defaultdict
from collections.abc import Callable  # Dict might not be used directly

from app.service_layer.message_bus import AbstractMessageBus, EventT

logger = logging.getLogger(__name__)


class InMemoryMessageBus(AbstractMessageBus[EventT]):
    """An in-memory message bus for handling domain events."""

    def __init__(self) -> None:
        """Initializes the InMemoryMessageBus with empty subscriptions."""
        self.subscriptions: defaultdict[
            type[EventT], list[Callable[[EventT], None]]
        ] = defaultdict(list)

    def publish(self, event: EventT) -> None:
        """
        Publishes an event to all subscribed handlers.

        Args:
            event: The domain event to publish.
        """
        event_type: type[EventT] = type(
            event
        )  # Removed type: ignore[assignment] as Mypy reported it unused
        if event_type in self.subscriptions:
            for handler in self.subscriptions[event_type]:
                try:
                    logger.debug(f"Handling event {event} with handler {handler}")
                    handler(event)
                except Exception:
                    logger.exception(f"Exception handling event {event}")
                    continue  # Or re-raise, or handle more gracefully

    def subscribe(
        self, event_type: type[EventT], handler: Callable[[EventT], None]
    ) -> None:
        """
        Subscribes a handler to a specific event type.

        Args:
            event_type: The type of domain event to subscribe to.
            handler: The callable handler to execute when the event is published.
        """
        self.subscriptions[event_type].append(handler)
        logger.info(f"Handler {handler} subscribed to {event_type}")
