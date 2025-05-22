# Service Layer Guide

This document outlines how we implement the Service Layer pattern to orchestrate domain logic and infrastructure.

## Core Components

### 1. Service Functions

```python
def allocate_order(
    order_id: str,
    sku: str,
    qty: int,
    uow: AbstractUnitOfWork,
    notify: AbstractNotifications,
) -> str:
    """Orchestrates the order allocation workflow."""
    with uow:
        product = uow.products.get(sku)
        if product is None:
            raise InvalidSku(sku)

        batch_ref = product.allocate(order_id, qty)
        uow.commit()

        notify.send_allocation_confirmed(order_id, batch_ref)
        return batch_ref
```

### 2. Message Handlers

```python
def add_stock(
    cmd: AddStock,
    uow: AbstractUnitOfWork,
    publish: Callable,
) -> None:
    """Command handler for adding new stock."""
    with uow:
        product = uow.products.get(cmd.sku)
        if product is None:
            product = Product(cmd.sku, batch_quantity=[])
            uow.products.add(product)

        product.add_batch(cmd.batch_ref, cmd.qty)
        uow.commit()
        publish(StockAdded(cmd.batch_ref, cmd.sku, cmd.qty))
```

## Implementation Patterns

1. **Dependencies via Arguments**
   - Accept infrastructure through parameters
   - Use dependency injection consistently
   - Allow for testing with fakes

2. **Atomic Operations**
   - Use Unit of Work context manager
   - Commit or rollback as one unit
   - Handle errors appropriately

3. **Clean Domain Integration**
   - Call domain model methods
   - Pass primitive types when possible
   - Keep business logic in domain

4. **Event Publishing**
   - Raise domain events after changes
   - Use publisher abstraction
   - Handle events after commit

## Testing Approach

```python
def test_allocate_order():
    # Arrange
    uow = FakeUnitOfWork()
    notify = FakeNotifications()
    add_stock_to_fake(uow, "LAMP", "batch1", 100)

    # Act
    result = service.allocate_order(
        "order1", "LAMP", 10, uow, notify
    )

    # Assert
    assert result == "batch1"
    assert notify.sent[0].order_id == "order1"
```

## Best Practices

1. **Keep Services Thin**
   - Orchestrate, don't implement
   - Delegate to domain model
   - Focus on workflow coordination

2. **Error Handling**
   - Use domain exceptions
   - Maintain invariants
   - Provide meaningful errors

3. **Use Case Focus**
   - One service function per use case
   - Clear purpose and name
   - Single responsibility

This guide provides patterns for implementing clean, maintainable service layers in our codebase.
