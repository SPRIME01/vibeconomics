# Testing Strategy Guide

This document outlines our testing approach using a pyramid structure of unit, integration, and end-to-end tests.

## Core Test Types

### 1. Unit Tests (Domain & Service Layer)

```python
def test_can_allocate_to_batch():
    """Test domain model behavior in isolation."""
    batch = Batch("batch1", "LAMP", 100)
    order_line = OrderLine("order1", "LAMP", 10)

    batch.allocate(order_line)

    assert batch.available_quantity == 90

def test_allocation_service():
    """Test service layer with fakes."""
    uow = FakeUnitOfWork()
    notify = FakeNotifications()

    service.allocate("order1", "LAMP", 10, uow, notify)

    assert uow.products.get("LAMP").available_quantity == 90
    assert notify.sent[0].order_id == "order1"
```

### 2. Integration Tests (Infrastructure)

```python
def test_sqlalchemy_repository(session):
    """Test real repository with database."""
    repo = SqlAlchemyRepository(session)
    product = Product("test-sku", "Test Lamp")

    repo.add(product)
    session.commit()

    rows = list(session.execute(
        'SELECT sku FROM products'
    ))
    assert rows == [("test-sku",)]

def test_email_notifications(smtp_server):
    """Test real notifications service."""
    notifications = EmailNotifications(smtp_server)

    notifications.send(
        "order1",
        "Order allocated to batch1"
    )

    assert len(smtp_server.sent_messages) == 1
```

### 3. End-to-End Tests (Full Stack)

```python
def test_api_allocate_order():
    """Test complete feature through API."""
    # Arrange
    add_stock_batch("batch1", "LAMP", 100)

    # Act
    response = test_client.post("/allocate", json={
        "order_id": "order1",
        "sku": "LAMP",
        "qty": 10
    })

    # Assert
    assert response.status_code == 200
    assert get_allocation("order1") == "batch1"
```

## Test Organization

1. **Directory Structure**
   ```
   tests/
   ├── unit/            # Fast tests with fakes
   │   ├── test_domain.py
   │   └── test_services.py
   ├── integration/     # Tests with real infrastructure
   │   ├── test_repository.py
   │   └── test_notifications.py
   └── e2e/            # Full system tests
       └── test_api.py
   ```

2. **Fixture Patterns**
   ```python
   @pytest.fixture
   def uow():
       """Clean fake UoW for testing."""
       return FakeUnitOfWork()

   @pytest.fixture
   def session():
       """Real database session for integration tests."""
       engine = create_engine(TEST_DB_URL)
       create_tables(engine)
       with Session(engine) as session:
           yield session
           session.rollback()
   ```
