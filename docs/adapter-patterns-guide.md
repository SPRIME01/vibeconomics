# Adapter Patterns Guide

This document outlines how we implement the Ports and Adapters (Hexagonal) architecture to interact with external systems and infrastructure.

## Core Principles

1. **Dependency Inversion:** High-level code (domain model, service layer) depends on abstractions, not implementation details
2. **Clean Boundaries:** Core business logic remains isolated from infrastructure concerns
3. **Explicit Interfaces:** External interactions happen through well-defined abstract interfaces (Ports)
4. **Pluggable Implementations:** Concrete adapters can be swapped without affecting core logic
5. **Infrastructure Independence:** Domain model has no knowledge of external systems

## Port Pattern (The Interface)

A Port defines the abstract interface that the core application uses to interact with external dependencies:

- **Definition:** An abstract contract specifying what operations are needed
- **Location:** Defined in the domain or service layer where it's needed
- **Implementation:** Use Python's `abc.ABC` to create Abstract Base Classes
- **Examples:**
  ```python
  class AbstractRepository(abc.ABC):
      @abc.abstractmethod
      def add(self, item: DomainModel) -> None: ...

      @abc.abstractmethod
      def get(self, id: str) -> Optional[DomainModel]: ...
  ```

## Adapter Pattern (The Implementation)

Adapters provide concrete implementations of Ports, translating between core application needs and external technology details:

- **Purpose:** Bridge between abstract ports and concrete infrastructure
- **Location:** Live in the infrastructure/adapters layer
- **Implementation:** Classes that inherit from and implement Port ABCs
- **Examples:**
  ```python
  class SqlAlchemyRepository(AbstractRepository):
      def __init__(self, session: Session):
          self.session = session

      def add(self, item: DomainModel) -> None:
          self.session.add(item)

      def get(self, id: str) -> Optional[DomainModel]:
          return self.session.query(DomainModel).filter_by(id=id).first()
  ```

## Common Adapter Types

1. **Repository Adapters**
   - Handle persistence (databases, file storage)
   - Translate between domain objects and storage format
   - Example: `SqlAlchemyRepository`, `FileSystemRepository`

2. **Messaging Adapters**
   - Handle external communication
   - Examples: `EmailNotifications`, `SmsGateway`

3. **API Client Adapters**
   - Interact with external services
   - Examples: `PaymentGateway`, `ShippingService`

4. **Entrypoint Adapters**
   - Handle incoming requests
   - Examples: `FastAPIHandler`, `CLICommand`

## Testing with Adapters

1. **Use Fake Implementations**
   - Create in-memory versions of adapters for testing
   - Implement same interface but use simple data structures
   - Example: `FakeRepository` using a dictionary for storage

2. **Test Real Adapters in Integration Tests**
   - Verify actual infrastructure interaction
   - Use test databases or sandboxed external services

## Best Practices

1. **Keep Adapters Thin**
   - Focus on translation between formats
   - No business logic in adapters
   - Simple 1:1 mapping where possible

2. **Use Dependency Injection**
   - Inject adapters through constructors or arguments
   - Configure concrete implementations in bootstrap code
   - Makes testing and swapping implementations easier

3. **Clear Separation**
   - Ports belong to the domain/service layer
   - Adapters belong to the infrastructure layer
   - No circular dependencies

4. **Error Handling**
   - Translate infrastructure errors to domain exceptions
   - Maintain domain language in error messages
   - Handle timeouts and connection issues appropriately

This guide provides the foundation for implementing clean, maintainable adapter patterns in our codebase.
