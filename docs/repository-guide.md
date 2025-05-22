# Repository Pattern Guide

This document describes how we implement the Repository pattern to abstract data persistence in our application.

## Core Components

### 1. Abstract Repository Interface

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.model import Product

class AbstractRepository(ABC):
    """Port/interface for data persistence."""

    @abstractmethod
    def add(self, product: Product) -> None:
        """Add a product to the repository."""
        pass

    @abstractmethod
    def get(self, reference: str) -> Optional[Product]:
        """Retrieve a product by its reference."""
        pass

    @abstractmethod
    def list(self) -> List[Product]:
        """List all products."""
        pass
```

### 2. Concrete Implementation

```python
class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, product: Product) -> None:
        self.session.add(product)

    def get(self, reference: str) -> Optional[Product]:
        return self.session.query(Product).filter_by(reference=reference).first()

    def list(self) -> List[Product]:
        return self.session.query(Product).all()
```

## Implementation Principles

1. **Domain-Infrastructure Bridge**
   - Acts as translator between domain model and storage
   - Domain model remains persistence-ignorant
   - Storage details isolated in repository implementation

2. **Collection-Like Interface**
   - Presents storage as in-memory collection
   - Simple, familiar methods (add, get, list)
   - Hides persistence complexity

3. **Single Aggregate Per Repository**
   - One repository class per aggregate root
   - Handles complete aggregate persistence
   - Maintains aggregate boundaries

## Usage Patterns

1. **With Unit of Work**
```python
def allocate_order(order_id: str, uow: AbstractUnitOfWork) -> str:
    with uow:
        product = uow.products.get(order_id)  # Get repository from UoW
        # ...use product...
        uow.commit()
```

2. **In Service Layer**
```python
class AllocationService:
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def allocate(self, order_id: str) -> None:
        with self.uow:
            products = self.uow.products.list()
            # ...allocation logic...
```

## Testing Support

### 1. Fake Repository
```python
class FakeRepository(AbstractRepository):
    def __init__(self):
        self._products: Dict[str, Product] = {}

    def add(self, product: Product) -> None:
        self._products[product.reference] = product

    def get(self, reference: str) -> Optional[Product]:
        return self._products.get(reference)
```

### 2. Integration Tests
```python
def test_repository_can_save_product(session):
    repo = SqlAlchemyRepository(session)
    product = Product("test-ref", "Test Product")

    repo.add(product)
    session.commit()

    rows = session.execute(
        text('SELECT reference, name FROM products')
    )
    assert list(rows) == [("test-ref", "Test Product")]
```

## Best Practices

1. **Keep Interface Simple**
   - Minimal methods needed for use cases
   - Collection-like operations
   - Clear naming reflecting domain concepts

2. **Maintain Encapsulation**
   - Hide storage implementation details
   - No ORM/database leakage into domain
   - Repository handles all persistence logic

3. **Support Testing**
   - Easy to create fake implementations
   - Integration tests with real storage
   - Clear verification methods

This guide provides patterns for implementing clean, maintainable repositories in our codebase.
