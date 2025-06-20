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
   - Handle asynchronous communication between different parts of the system or with external systems via message queues.
   - Decouple services and improve resilience.
   - Examples in general systems: `EmailNotifications`, `SmsGateway`.
   - Example in this project: `RabbitMQMessageBus`.

   ### `RabbitMQMessageBus`

   The `RabbitMQMessageBus` provides a concrete implementation of the `AbstractMessageBus` interface (defined in the service layer) for asynchronous event handling using RabbitMQ.

   **Purpose and Functionality:**
   - **Asynchronous Event Handling:** Enables different parts of the application to communicate by publishing events and handling them asynchronously.
   - **Publishing Events:** Allows services to publish `DomainEvent` instances to RabbitMQ.
   - **Handler Registration:** Services can register handler functions to consume specific types of events from dedicated RabbitMQ queues.
   - **Reliability Features:**
     - **Durable Queues:** Ensures that queues survive broker restarts.
     - **Persistent Messages:** Marks messages as persistent to ensure they are not lost if the broker restarts. This is configured during publishing.
     - **Manual Acknowledgments:** Requires consumers to explicitly acknowledge (ACK) or negatively acknowledge (NACK) messages, ensuring that messages are properly processed or can be dead-lettered/re-queued based on policy if processing fails.

   **Setup and Configuration:**
   - **RabbitMQ Instance:** A running RabbitMQ instance is required. For installation and setup, refer to the [RabbitMQ Official Website](https://www.rabbitmq.com/download.html).
   - **Configuration (`RabbitMQConfig`):**
     - The connection parameters for RabbitMQ are managed by the `RabbitMQConfig` class found in `app.adapters.rabbitmq_config`.
     - Key parameters include:
       - `host`: Hostname of the RabbitMQ server (default: "localhost").
       - `port`: Port number for the RabbitMQ server (default: 5672).
       - `username`: Optional username for authentication.
       - `password`: Optional password for authentication.
       - `virtual_host`: The virtual host to use (default: "/").
     - These parameters are typically loaded from environment variables (e.g., `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASS`, `RABBITMQ_VHOST`) into an application settings object (e.g., `app.config.Settings`), which then populates `RabbitMQConfig`.

   **Code Example:**

   The following conceptual example illustrates how to instantiate and use the `RabbitMQMessageBus`:

   ```python
   # Conceptual Example (actual connection setup might vary based on application structure)
   import pika
   from app.adapters.rabbitmq_message_bus import RabbitMQMessageBus
   from app.core.base_aggregate import DomainEvent

   # --- Define a sample event ---
   class UserRegistered(DomainEvent):
       user_id: int
       email: str

   # --- Define a sample handler (must be synchronous for pika.BlockingConnection) ---
   def handle_user_registered(event: UserRegistered):
       # This handler is synchronous. If you need to perform async operations,
       # see the note below.
       print(f"Handling UserRegistered event for user_id: {event.user_id}, email: {event.email}")

   # --- RabbitMQ Connection (example, typically managed by a factory or DI container) ---
   # Example:
   # rabbitmq_config = RabbitMQConfig(
   #     host=settings.RABBITMQ_HOST,
   #     port=settings.RABBITMQ_PORT,
   #     username=settings.RABBITMQ_USER, # Assuming these exist in settings
   #     password=settings.RABBITMQ_PASS,
   #     virtual_host=settings.RABBITMQ_VHOST
   # )
   #
   # credentials = None
   # if rabbitmq_config.username:
   #     credentials = pika.PlainCredentials(rabbitmq_config.username, rabbitmq_config.password)
   #
   # parameters = pika.ConnectionParameters(
   #     host=rabbitmq_config.host,
   #     port=rabbitmq_config.port,
   #     virtual_host=rabbitmq_config.virtual_host,
   #     credentials=credentials
   # )
   # connection = pika.BlockingConnection(parameters) # Message bus uses a blocking connection

   # # --- Instantiate the bus (assuming a valid pika.BlockingConnection is provided) ---
   # # message_bus = RabbitMQMessageBus(connection=connection)

   # --- Register a handler ---
   # Handlers registered with RabbitMQMessageBus must be synchronous functions.
   # Do not use 'async def' handlers unless you manage the event loop yourself.
   message_bus.register_handler(UserRegistered, handle_user_registered)

   # # --- Publish an event ---
   # async def publish_example():
   #     new_user_event = UserRegistered(user_id=1, email="test@example.com")
   #     # await message_bus.publish(new_user_event) # Publishing is an async operation
   #     print("Event published (conceptually)")

   # # --- Running Consumers ---
   # # To consume messages, a separate process or thread is usually dedicated to running
   # # the consumer loop. After handlers are registered, this process would start consuming.
   # # For example, a simplified consumer startup might look like:
   # #
   # # def start_consumer_process():
   # #     # (connection and bus setup as above)
   # #     message_bus.register_handler(UserRegistered, handle_user_registered)
   # #
   # #     # Get a channel from the connection for this consumer.
   # #     # The RabbitMQMessageBus itself creates channels for operations, but for a
   # #     # long-running consumer, you might manage a channel explicitly or use
   # #     # the bus's connection to create one dedicated to consuming.
   # #     # For pika.BlockingConnection, channel.start_consuming() is a blocking call.
   # #     # It's often run in its own thread or process.
   # #
   # #     try:
   # #         print("Consumer starting... waiting for messages.")
   # #         # The bus's register_handler already calls basic_consume.
   # #         # To keep the connection alive and processing events,
   # #         # for a BlockingConnection, you might need to periodically process data events
   # #         # or run channel.start_consuming() if you manage the channel explicitly
   # #         # for consumption outside of the bus's direct control.
   # #         # However, the current bus design with BlockingConnection implicitly handles
   # #         # consumption on channels created by register_handler when pika's I/O loop is processed.
   # #         # For a dedicated consumer, ensuring the connection's I/O loop is running is key.
   # #         # A simple way for BlockingConnection if not managing threads explicitly:
   # #         # while True:
   # #         #     connection.process_data_events(time_limit=1) # Process events regularly
   # #
   # #         # If using a dedicated channel for consuming:
   # #         # consumer_channel = connection.channel()
   # #         # # Assuming queue is declared and consumer is set up on this channel by register_handler
   # #         # consumer_channel.start_consuming() # This will block
   # #     except KeyboardInterrupt:
   # #         print("Consumer stopped.")
   # #     finally:
   # #         if 'connection' in locals() and connection.is_open:
   # #             connection.close()
   # #
   # # if __name__ == "__main__":
   # #     # To run publisher:
   # #     # asyncio.run(publish_example())
   # #     # To run consumer (conceptual, would be a separate script/service):
   # #     # start_consumer_process()
   # #     pass
   ```

   **Note on Asynchronous Handlers:**

   `RabbitMQMessageBus` uses `pika.BlockingConnection`, which expects synchronous callbacks for message consumption. If you register an `async def` handler, Pika will call it as a regular function, returning a coroutine object that will not be awaited or executed. This means your async handler will not run as intended.

   If you need to perform asynchronous operations in a handler, you have two options:
   1. **Delegate to a thread pool or run the coroutine in a new event loop:**
      You can use `asyncio.run()` or `asyncio.get_event_loop().run_until_complete()` inside the synchronous handler, but this is generally discouraged unless you are certain about event loop management and thread safety.
   2. **Offload work to a background thread or task queue:**
      For I/O-bound or async work, consider submitting the task to a thread pool or a background worker.

   **Best Practice:**
   Write synchronous handler functions for use with `RabbitMQMessageBus` and `pika.BlockingConnection`. If you need to call async code, wrap it appropriately:

   ```python
   import asyncio

   def handle_user_registered(event: UserRegistered):
       # If you must call async code, do so explicitly:
       asyncio.run(async_handler(event))  # Not recommended if already in an event loop

   async def async_handler(event: UserRegistered):
       # ...async logic...
       pass
   ```

   However, for most use cases, keep handlers synchronous to avoid event loop issues.

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
