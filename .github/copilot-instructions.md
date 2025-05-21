# Copilot Instructions

This file provides GitHub Copilot with high-level context about this project's architecture, principles, and coding standards.

## Project Overview

[Project Name] is a [brief description of the project].

## General Architectural Principles

This project follows several key architectural principles:

*   **Dependency Inversion Principle (DIP):** High-level modules (like domain and service layers) should not depend on low-level modules (like specific database or external service implementations). Both should depend on **abstractions**. Concrete implementations (adapters) depend on abstract interfaces (ports) defined by higher layers.
*   **Domain-Driven Design (DDD):** This project uses DDD to model the core business problem and ensure code reflects the business language (ubiquitous language). The focus is on understanding and implementing the complex logic within the domain.
*   **Separation of Concerns:** Responsibilities are clearly separated into distinct layers and components to manage complexity and improve maintainability. Core business logic is isolated from infrastructure details.
*   **Encapsulation:** Objects and components are designed to hide their internal state and expose behavior through well-defined interfaces.
*   **Persistence Ignorance:** The core domain model should not have any knowledge of how it is saved or loaded. This concern is handled by the infrastructure layer, specifically repositories.
*   **Infrastructure as Details:** Specific technology choices for things like databases, messaging, or web frameworks are treated as interchangeable details that the core architecture should not be coupled to. This architecture is designed to make swapping out infrastructure components feasible.

## Architectural Layers

This project is structured into distinct layers:

*   **Domain Layer:** This is the **core** of the application. It contains the essential business logic, including Entities, Value Objects, and Aggregates. It should have **no external dependencies** on infrastructure. Domain Events are defined within this layer to represent significant occurrences.
*   **Service Layer:** This layer defines the application's use cases and orchestrates interactions between the domain model and the infrastructure. It acts as the **entrypoint to the domain** from the outside world. Service logic interacts with the domain and infrastructure via **abstractions** like Repositories and the Unit of Work. Service functions often evolve into or are implemented as message Handlers in an event-driven setup.
*   **Adapters/Infrastructure Layer:** This layer contains the **concrete implementations** of interfaces defined in higher layers. This includes database repositories (e.g., using SQLModel, TypeORM, Prisma), external service clients, message bus implementations, notification senders, etc. These components depend on the abstract 'ports' defined elsewhere.
*   **Entrypoints:** These are the **outermost layer** that drives the application. Examples include FastAPI handlers, Express.js routes, command-line interface (CLI) scripts, or message consumers. Entrypoints should be **thin**; their primary job is to receive external requests, translate them into domain messages (Commands or Events) or function calls, and pass them to the Service Layer or Message Bus. They handle input/output translation and validation at the edge.
*   **Message Bus:** A central mechanism responsible for dispatching messages (Commands and Events) to their corresponding Handlers. It facilitates communication and decoupling between different parts of the system and potentially between services.
*   **Bootstrap (Composition Root):** This component is responsible for **initializing and wiring together dependencies** (like the Unit of Work, repositories, message bus, adapters) at application startup. Entrypoints typically obtain the necessary core object (like the message bus or main service entrypoint) from the bootstrap.

## General Coding Standards and Conventions

This project follows standard coding conventions for both Python and TypeScript/JavaScript, as well as project-specific rules:

*   **Naming:** Use descriptive names that align with the ubiquitous language.
    * For Python: Follow standard conventions for variables, functions (snake_case), classes (PascalCase), etc.
    * For TypeScript/JavaScript: Use camelCase for variables and functions, PascalCase for classes and types, and UPPER_CASE for constants.
*   **Formatting:** Adhere to project-wide formatting rules (e.g., using a linter like Ruff or Black for Python, Prettier or ESLint for TypeScript/JavaScript). (Specific rules like indentation or quotes can be added here if they deviate significantly or are critical, e.g., "Use 4 spaces for indentation").
*   **Type Hints / Type Annotations:**
    * For Python: Use type hints consistently to improve code clarity, documentation, and enable static analysis.
    * For TypeScript: Use type annotations and interfaces to ensure type safety and clarity.
*   **Immutability:** Value Objects and Domain Events should be **immutable** data structures.
    * For Python: Use `frozen=True` dataclasses or namedtuples.
    * For TypeScript/JavaScript: Use `readonly` properties, `Readonly` types, or `Object.freeze` where appropriate.
*   **Dataclasses / Data Structures:**
    * For Python: Prefer dataclasses for simple data structures, especially Value Objects and Events, as they provide built-in methods like `__init__`, `__eq__`, and `__repr__`.
    * For TypeScript: Use interfaces, types, or classes for data structures. Prefer `readonly` for immutability.
*   **Abstract Base Classes (ABCs) / Interfaces:**
    * For Python: Define interfaces for dependencies (ports) using Python's typing.protocol except where the `abc` module is more appropriate. Concrete implementations (adapters) inherit from and implement these protocols and ABCs.
    * For TypeScript: Use `interface` or `abstract class` to define contracts for dependencies. Concrete implementations must implement these interfaces.
*   **Tests:** This project prioritizes a strong test suite following a Test Pyramid approach, aiming for many fast unit/service tests using fakes and fewer integration/E2E tests. Tests should reflect the ubiquitous language where possible.
    * For Python: Use pytest.
    * For TypeScript/JavaScript: Use vitest.
    * Use Playwright for E2E tests.

This file provides the foundational context. More detailed guidance on specific patterns (like how to implement a Fake Unit of Work or specific rules for Aggregate boundaries) should be in the docs/ directory and referenced in .vscode/settings.json. Task-specific instructions, like templates for generating a new handler or repository, belong in the .github/prompts/ directory.
