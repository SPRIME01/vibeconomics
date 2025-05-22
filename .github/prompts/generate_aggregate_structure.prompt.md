# Generate Aggregate Structure

**Goal:** Generate a new Aggregate Root class and its contained objects that form a consistency boundary in the domain model.

**Instructions:**

1.  Create a Python class for the Aggregate Root (which must be an Entity).
2.  Define any contained Entities or Value Objects that belong to this aggregate.
3.  Ensure contained objects can only be accessed and modified through the Aggregate Root.
4.  Implement methods on the Aggregate Root that represent key domain operations.
5.  Add validation logic to enforce business rules (invariants) across the group of objects.
6.  Place all aggregate-related classes in the appropriate domain module.
7.  Ensure the aggregate follows DDD principles:
    *   All changes must go through the Aggregate Root
    *   Maintain consistency within the boundary
    *   Enforce invariants during state changes
    *   Use domain language in naming
    *   Consider transactional boundaries

**Context:**

*   Aggregate Root name: `[AGGREGATE_ROOT_NAME]` (e.g., `Product`)
*   Contained Objects:
    *   `[OBJECT_1_NAME]` (Entity/Value Object, e.g., `Batch`)
    *   `[OBJECT_2_NAME]` (Entity/Value Object)
*   Key Behaviors:
    *   `[METHOD_1]([PARAMS])` - describe operation (e.g., `allocate_order`)
    *   `[METHOD_2]([PARAMS])` - describe operation
*   Business Rules:
    *   `[RULE_1]` (e.g., "total allocated quantity cannot exceed batch quantity")
    *   `[RULE_2]`
*   Module location: `src/allocation/domain/model.py`

Generate the Python code for the `[AGGREGATE_ROOT_NAME]` aggregate structure.
