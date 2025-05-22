# Domain Modeling Rules and Principles

This document outlines the principles for modeling the core business domain in this project, based on Domain-Driven Design (DDD).

## 1. Foundation: Ubiquitous Language

* We strive to use the precise language of our business experts consistently throughout the codebase, tests, and communication. This "ubiquitous language" ensures everyone understands the concepts the same way.
* Terms like "Batch", "OrderLine", "Product", "SKU", "allocation" are fundamental business concepts that must be reflected directly in class names, variable names, and method names.
* Domain exceptions should also be named in the ubiquitous language.

## 2. Core Building Blocks: Entities, Value Objects, and Aggregates

Our domain model is composed of these fundamental patterns:

* **Entities:**
  * Represent core business objects that have a unique identity and lifecycle.
  * Identity is the primary characteristic; two entities are considered different if their identities differ, even if all their attributes are the same.
  * They can have mutable state and behavior that changes that state.
  * Examples: `Batch`, `OrderLine`, `Product` (as an Aggregate Root).

* **Value Objects:**
  * Represent descriptive concepts or values without conceptual identity.
  * They are defined by their attributes; two Value Objects with the same attributes are considered equal ("structural equality").
  * **They must be immutable**. Any "change" results in a new Value Object instance.
  * Examples: `Quantity`, `Sku` (if treated as a value rather than an entity reference), possibly address or money objects.
  * Prefer Python `dataclasses` for simple Value Objects.

* **Aggregates:**
  * Define a **consistency boundary** around a group of related Entities and Value Objects.
  * One Entity within the aggregate is designated as the **Aggregate Root**. All external interactions with the aggregate must go through the root.
  * The Aggregate Root is responsible for enforcing all **invariants** (business rules) that apply across the objects within its boundary.
  * Choosing the right aggregate is crucial for maintaining data integrity and managing complexity. It influences transaction boundaries and concurrency.
  * Example: `Product` is the aggregate root for its contained `Batch` objects. Changes to `Batch`es related to allocation should happen via methods on the `Product` aggregate.

## 3. Domain Layer Characteristics

* The domain layer is the **core** of the application and contains the essential business logic and domain model.
* It must have **no external dependencies**. It should not depend on infrastructure details like databases, web frameworks, or external services. Dependencies should point *inwards* towards the domain (Dependency Inversion Principle - DIP).
* Domain objects should be **behavior-rich**, encapsulating their state and behavior rather than being "anemic" data structures.

## 4. Modeling Best Practices

* Apply general Object-Oriented design principles (SOLID, composition over inheritance).
* Use type hints to document expected arguments and improve clarity.
* Exceptions should convey domain concepts.
* Consider Domain Events as a way to signal that something significant has happened within the domain, decoupling side effects.

By adhering to these rules, we aim to build a domain model that is a clear, testable representation of our business problem, independent of infrastructure concerns.
