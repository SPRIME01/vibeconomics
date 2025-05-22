# Refactoring Guide

This document outlines our approach to improving existing code through systematic refactoring.

## Core Principles

1. **Start with Tests**

   First, write tests that capture existing behavior

   ```python
   def test_existing_allocation_behavior():
       batch = Batch("batch1", "LAMP", 100)
       line = OrderLine("order1", "LAMP", 10)
       assert batch.can_allocate(line)
   ```

2. **Extract and Abstract**

   Before: Mixed responsibilities

   ```python
   def allocate_stock(order_id: str, sku: str, qty: int) -> str:
       with Session() as session:
           batch = session.query(Batch).filter_by(sku=sku).first()
           line = OrderLine(order_id, sku, qty)
           batch.allocate(line)
           session.commit()
           return batch.reference
   ```

   After: Separated concerns with clear dependencies

   ```python
   def allocate_stock(
       order_id: str,
       sku: str,
       qty: int,
       uow: AbstractUnitOfWork,
   ) -> str:
       with uow:
           batch = uow.batches.get(sku)
           line = OrderLine(order_id, sku, qty)
           batch.allocate(line)
           uow.commit()
           return batch.reference
   ```

## Refactoring Patterns

1. **Extract Service Layer**
   - Move business logic out of entrypoints
   - Create service functions that accept dependencies
   - Keep entrypoints thin and focused on I/O

2. **Introduce Abstractions**
   - Define interfaces (ABCs) for infrastructure concerns
   - Create fake implementations for testing
   - Inject dependencies rather than creating them

3. **Split by Responsibility**
   - Separate domain logic from infrastructure
   - Move related code into cohesive modules
   - Create focused classes and functions

## Step-by-Step Process

1. **Preparation**
   - Write tests covering existing behavior
   - Identify code smells and pain points
   - Plan the target architecture

2. **Implementation**
   - Make small, reversible changes
   - Run tests after each change
   - Commit frequently with clear messages

3. **Validation**
   - Verify behavior hasn't changed
   - Check test coverage
   - Review for architectural alignment

## Common Refactoring Types

1. **Infrastructure Separation**

   Before: Direct database dependency

   ```python
   def get_products():
       return session.query(Product).all()
   ```

   After: Repository abstraction

   ```python
   class AbstractRepository(abc.ABC):
       @abc.abstractmethod
       def get(self, reference) -> Product: ...

   def get_products(repo: AbstractRepository):
       return repo.get_all()
   ```

2. **Service Extraction**

   Before: Logic in API handler

   ```python
   @app.post("/allocate")
   def allocate_endpoint(order_id: str, sku: str, qty: int):
       # ...complex allocation logic...
   ```

   After: Thin endpoint calling service

   ```python
   @app.post("/allocate")
   def allocate_endpoint(order_id: str, sku: str, qty: int):
       cmd = commands.Allocate(order_id, sku, qty)
       bus.handle(cmd)
   ```

## Best Practices

1. **Keep Changes Small**
   - Make one type of change at a time
   - Use version control effectively
   - Run tests frequently

2. **Maintain Behavior**
   - Start with thorough tests
   - Refactor structure, not behavior
   - Verify through test coverage

3. **Follow Architecture**
   - Move toward cleaner layers
   - Use dependency injection
   - Keep domain logic pure

This guide provides patterns and examples for improving code structure while maintaining correctness.
