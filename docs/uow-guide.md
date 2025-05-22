# Unit of Work (UoW) Guide

This document outlines how we implement the Unit of Work pattern to manage transactional consistency.

## Core Components

### 1. Abstract UoW Interface

```python
from abc import ABC, abstractmethod
from typing import Optional
from domain.model import Product

class AbstractUnitOfWork(ABC):
    """Port/interface for transaction management."""
    products: AbstractRepository  # Repository property

    @abstractmethod
    def __enter__(self) -> "AbstractUnitOfWork":
        """Start a new transaction and return self."""
        pass

    @abstractmethod
    def __exit__(self, *args):
        """Roll back transaction if not committed."""
        self.rollback()

    @abstractmethod
    def commit(self):
        """Commit the current transaction."""
        pass

    @abstractmethod
    def rollback(self):
        """Roll back the current transaction."""
        pass
```

### 2. Concrete Implementation

```python
class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.products = SqlAlchemyRepository(self.session)
        return self

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
```

## Usage Patterns

### 1. In Service Layer

```python
def allocate_order(
    order_id: str,
    sku: str,
    qty: int,
    uow: AbstractUnitOfWork
) -> str:
    """Use UoW to manage transaction boundary."""
    with uow:
        product = uow.products.get(sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {sku}")

        batch_ref = product.allocate(order_id, qty)
        uow.commit()
        return batch_ref
```

### 2. With Event Collection

```python
class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory, collect_events):
        self.session_factory = session_factory
        self.collect_events = collect_events

    def commit(self):
        for product in self.products.seen:
            while product.events:
                self.collect_events(product.events.pop(0))
        self.session.commit()
```

## Testing Support

### 1. Fake Implementation

```python
class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        pass
```

### 2. Service Layer Tests

```python
def test_allocate_order():
    # Arrange
    uow = FakeUnitOfWork()
    add_stock_to_fake(uow, "LAMP", "batch1", 100)

    # Act
    result = service.allocate_order(
        "order1", "LAMP", 10, uow
    )

    # Assert
    assert result == "batch1"
    assert uow.committed
```

## Best Practices

1. **Transaction Management**
   - Use context manager (`with` block)
   - Always commit or rollback
   - Handle exceptions properly

2. **Repository Access**
   - Get repositories from UoW
   - Keep repositories private
   - Access via properties

3. **Event Handling**
   - Collect events before commit
   - Publish after successful commit
   - Clear collected events

This guide provides patterns for implementing clean, maintainable Unit of Work pattern in our codebase.
