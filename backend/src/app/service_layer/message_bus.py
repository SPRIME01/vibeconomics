import abc
from collections.abc import Callable
from typing import Generic, TypeVar

from app.core.base_aggregate import DomainEvent  # Adjusted import

EventT = TypeVar("EventT", bound=DomainEvent)


class AbstractMessageBus(abc.ABC, Generic[EventT]):
    """
    Abstract base class for a message bus, responsible for handling and dispatching events.

    Attributes:
        subscriptions: A dictionary mapping event types to a list of handler functions.
                       It is recommended to initialize this in concrete implementations.
                       Example: self.subscriptions = defaultdict(list)
    """

    # subscriptions: Dict[Type[EventT], List[Callable[[EventT], None]]]

    @abc.abstractmethod
    def publish(self, event: EventT) -> None:
        """
        Publishes an event to all subscribed handlers.

        Args:
            event: The domain event to publish.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def subscribe(
        self, event_type: type[EventT], handler: Callable[[EventT], None]
    ) -> None:
        """
        Subscribes a handler to a specific event type.

        Args:
            event_type: The type of the event to subscribe to.
            handler: The callable function that will handle the event.
        """
        raise NotImplementedError
