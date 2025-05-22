# Dependency Injection and Bootstrap Guide

This document outlines our approach to managing dependencies and application composition.

## Core Concepts

1. **Dependencies Flow Inward**
   - Core domain code has no external dependencies
   - Infrastructure adapters depend on domain interfaces
   - Components receive dependencies, never create them

2. **Composition Root Pattern**
   - Single place (`bootstrap.py`) for wiring dependencies
   - Creates and connects all components
   - Only place that knows about concrete implementations

## Implementation Patterns

### 1. Defining Dependencies

```python
# Abstract interfaces (ports) in domain/service layer
class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, item: Product) -> None: ...

    @abc.abstractmethod
    def get(self, reference: str) -> Optional[Product]: ...

# Concrete implementation in infrastructure layer
class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session
```

### 2. Injecting Dependencies

```python
# Service functions accept dependencies as arguments
def allocate_order(
    order_line: OrderLine,
    uow: AbstractUnitOfWork,
    notify: AbstractNotifications,
) -> str:
    with uow:
        product = uow.products.get(order_line.sku)
        product.allocate(order_line)
        uow.commit()
```

### 3. Bootstrap Script

```python
# bootstrap.py - Composition Root
def bootstrap(
    start_orm: bool = True,
    uow: AbstractUnitOfWork | None = None,
    notifications: AbstractNotifications | None = None,
    publish: Callable = lambda *args: None,
) -> MessageBus:
    """Initialize and wire up the application components."""

    if start_orm:
        orm.start_mappers()

    if uow is None:
        session_factory = sessionmaker(bind=create_engine(config.get_postgres_uri()))
        uow = SqlAlchemyUnitOfWork(session_factory)

    if notifications is None:
        notifications = EmailNotifications()

    # Wire up the message bus with its handlers
    bus = MessageBus()
    bus.register(
        commands.Allocate,
        lambda cmd: handlers.allocate(cmd, uow, notifications),
    )
    return bus
```

## Best Practices

1. **Keep Dependencies Explicit**
   - Pass dependencies as arguments
   - Use type hints to document dependencies
   - Avoid global state and service locators

2. **Favor Constructor Injection**
   ```python
   class AllocationHandler:
       def __init__(self, uow: AbstractUnitOfWork):
           self.uow = uow
   ```

3. **Use Dependency Injection for Testing**
   ```python
   def test_allocate_order():
       uow = FakeUnitOfWork()
       notify = FakeNotifications()
       result = service.allocate_order(order_line, uow, notify)
   ```

4. **Bootstrap Configuration**
   - Allow overriding defaults for testing
   - Support different environments
   - Keep bootstrap code thin and declarative

## Key Principles

1. **Manual Over Framework**
   - Use explicit dependency passing
   - Bootstrap script handles wiring
   - Consider DI framework only if complexity grows significantly

2. **Clear Dependency Flow**
   - Domain defines interfaces
   - Infrastructure provides implementations
   - Bootstrap connects everything
   - Tests use fake implementations

This guide provides the foundation for implementing clean, maintainable dependency injection in our codebase.
