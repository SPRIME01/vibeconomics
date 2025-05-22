# Event-Driven Architecture Guide

This document outlines how we implement event-driven patterns in our application.

## Core Components

### 1. Message Types

#### Commands

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class AllocateOrder:
    """Command to allocate an order to available stock."""
    order_id: str
    sku: str
    qty: int

@dataclass(frozen=True)
class CancelAllocation:
    """Command to cancel an existing allocation."""
    order_id: str
    sku: str
```

#### Events

```python
@dataclass(frozen=True)
class OrderAllocated:
    """Event indicating an order was successfully allocated."""
    order_id: str
    sku: str
    qty: int
    batch_reference: str

@dataclass(frozen=True)
class AllocationFailed:
    """Event indicating allocation could not be completed."""
    order_id: str
    sku: str
    reason: str
```

### 2. Message Bus Implementation

```python
class MessageBus:
    def __init__(self):
        self._command_handlers = {}  # type: dict
        self._event_handlers = defaultdict(list)

    def handle(self, message: Union[Command, Event]) -> Any:
        """Route message to appropriate handler(s)."""
        if isinstance(message, Command):
            return self._handle_command(message)
        return self._handle_event(message)

    def register_command(
        self,
        command_type: Type[Command],
        handler: Callable[[Command], Any]
    ) -> None:
        """Register a single handler for a command type."""
        if command_type in self._command_handlers:
            raise ValueError(f"Handler already registered for {command_type}")
        self._command_handlers[command_type] = handler
```

### 3. Handler Patterns

```python
# Command Handler
def allocate(
    cmd: AllocateOrder,
    uow: AbstractUnitOfWork,
    publish: Callable,
) -> str:
    """Handle allocation command, return batch reference."""
    with uow:
        product = uow.products.get(cmd.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {cmd.sku}")

        try:
            batch_ref = product.allocate(cmd.order_id, cmd.sku, cmd.qty)
            uow.commit()
            publish(OrderAllocated(cmd.order_id, cmd.sku, cmd.qty, batch_ref))
            return batch_ref
        except OutOfStock:
            publish(AllocationFailed(cmd.order_id, cmd.sku, "out of stock"))
            raise

# Event Handler
def notify_allocation(event: OrderAllocated, notify: AbstractNotifications) -> None:
    """Send notification when order is allocated."""
    notify.send_email(
        "warehouse@made.com",
        f"Order {event.order_id} allocated to {event.batch_reference}"
    )
```

## Implementation Patterns

1. **Command Handling**
   - One handler per command type
   - Handle-or-fail semantics
   - Return results directly
   - Raise domain exceptions

2. **Event Handling**
   - Multiple handlers allowed
   - Fire-and-forget semantics
   - No return values
   - Handle failures independently

3. **Message Flow**
   - Commands flow down
   - Events flow up and out
   - Commands modify state
   - Events notify of changes

4. **Dependencies**
   - Inject via constructor/arguments
   - Use abstractions (UoW, Notifications)
   - Allow for testing with fakes
   - Pass publisher function for events

## Testing Approach

1. **Command Handler Tests**

```python
def test_allocate_command():
    uow = FakeUnitOfWork()
    publish = Mock()

    result = allocate(
        AllocateOrder("order1", "LAMP", 10),
        uow,
        publish
    )

    assert result == "batch1"
    assert publish.called_with(OrderAllocated("order1", "LAMP", 10, "batch1"))
```

2. **Event Handler Tests**

```python
def test_notification_handler():
    notifications = FakeNotifications()

    notify_allocation(
        OrderAllocated("order1", "LAMP", 10, "batch1"),
        notifications
    )

    assert len(notifications.sent) == 1
    assert notifications.sent[0].destination == "warehouse@made.com"
```

This guide provides patterns and examples for implementing clean, maintainable event-driven architecture in our codebase.
