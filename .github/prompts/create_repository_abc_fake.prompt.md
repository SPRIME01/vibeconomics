# Create Repository ABC and Fake Implementation

**Goal:** Generate the Python Abstract Base Class (ABC) for a new Repository and an in-memory Fake implementation for testing.

**Instructions:**

1.  Create a Python Abstract Base Class (ABC) for the new repository.
2.  Inherit from `abc.ABC`.
3.  Define abstract methods for the core repository operations required for this entity/aggregate. Common methods include:
    *   `add(entity)`: Add a new entity to storage.
    *   `get(reference)`: Retrieve an entity by its identifier/reference.
    *   `list()`: Retrieve all entities (use cautiously in real implementations).
    *   Consider methods like `save(entity)` or `update(entity)` if needed, though often `add` handles initial save and subsequent changes are tracked by the Unit of Work.
4.  The abstract methods should define type hints for the entity/aggregate type they handle and their return types.
5.  Create an in-memory Fake implementation of this ABC.
6.  The Fake implementation should store entities in a simple Python data structure (e.g., a list or dictionary) to simulate persistence for tests [7].
7.  Implement all abstract methods in the Fake class using the in-memory storage.
8.  Ensure both the ABC and Fake implementation are placed within the `src/allocation/adapters/repository.py` file (or similar adapters module) [3, 8].
9.  Reference the `repository-guide.md` document for detailed principles on repository implementation in this project.

**Context:**

*   Entity/Aggregate name: [ENTITY_NAME] (e.g., Product, Batch)
*   Key identifier/reference attribute: [REFERENCE_ATTRIBUTE] (e.g., sku, reference)
*   Location for files: `src/allocation/adapters/repository.py`

Generate the Python code for the `[ENTITY_NAME]Repository` ABC and `Fake[ENTITY_NAME]Repository`.
