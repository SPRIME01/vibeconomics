# Test Doubles Guide

This document outlines how we use Test Doubles in our testing strategy, with a focus on Fakes.

## Core Test Double Types

### 1. Fake Implementation

```python
class FakeProductRepository(AbstractRepository):
    """In-memory fake for testing."""
    def __init__(self):
        self._products: Dict[str, Product] = {}

    def add(self, product: Product) -> None:
        self._products[product.reference] = product

    def get(self, reference: str) -> Optional[Product]:
        return self._products.get(reference)
```

### 2. Mock (Use Sparingly)

```python
# Prefer state verification with Fakes over behavior verification with mocks
@pytest.fixture
def publish():
    """Example where a mock makes sense for verification."""
    return Mock()

def test_publishes_allocated_event():
    # Arrange
    uow = FakeUnitOfWork()
    publish = Mock()

    # Act
    handlers.allocate(cmd, uow, publish)

    # Assert - verifying outbound messages is an acceptable mock use case
    publish.assert_called_once_with(
        events.Allocated(cmd.order_id, cmd.sku)
    )
```

## Implementation Patterns

1. **Using Fakes for Infrastructure**
```python
class FakeUnitOfWork:
    def __init__(self):
        self.products = FakeProductRepository()
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass
```

2. **Testing with Fakes**
```python
def test_allocate_order():
    # Arrange - using fakes for clean, fast tests
    uow = FakeUnitOfWork()
    notify = FakeNotifications()

    # Act
    service.allocate_order("order1", "LAMP", 10, uow, notify)

    # Assert - verify state changes
    product = uow.products.get("LAMP")
    assert product.available_quantity == 90
```

## Best Practices

1. **Prefer Fakes Over Mocks**
   - Use in-memory implementations
   - Verify state over behavior
   - Keep fakes simple but functional

2. **State Over Behavior Verification**
   ```python
   # Good: Verify final state
   assert uow.products.get(sku).available_quantity == 90

   # Avoid: Verifying implementation details
   mock_repo.allocate.assert_called_with(order_line)
   ```

3. **Exception Handling**
   ```python
   class FakeNotifications:
       def __init__(self):
           self.sent = []
           self.failed = []

       def send_email(self, to: str, body: str) -> None:
           try:
               # Simulate sending
               self.sent.append({"to": to, "body": body})
           except Exception as e:
               self.failed.append({"to": to, "error": str(e)})
   ```

This guide provides patterns for implementing clean, maintainable test doubles in our codebase.
