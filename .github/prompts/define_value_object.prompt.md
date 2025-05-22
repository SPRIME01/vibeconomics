# Define Value Object Class

**Goal:** Generate a new Value Object class that represents an immutable concept or value in the domain model.

**Instructions:**

1.  Create a Python dataclass for the new Value Object.
2.  Use `@dataclass(frozen=True)` to ensure immutability.
3.  Define type-hinted attributes based on the ubiquitous language of the domain.
4.  Methods should not modify state; instead, they should return new instances.
5.  Equality is based on attribute values (structural equality), which dataclass handles automatically.
6.  Ensure the class follows Value Object principles:
    *   No identity - equality based on attributes
    *   Complete immutability
    *   Self-validation in __post_init__ if needed
    *   Methods return new instances rather than modifying state
7.  Place the Value Object class in the appropriate domain module (e.g., `src/allocation/domain/model.py`).

**Context:**

*   Value Object name: [VALUE_OBJECT_NAME] (e.g., Money, Quantity)
*   Attributes:
    *   [ATTRIBUTE_1]: [TYPE]
    *   [ATTRIBUTE_2]: [TYPE]
*   Optional Methods:
    *   [METHOD_1]([PARAMS]) -> returns new instance
    *   [METHOD_2]([PARAMS]) -> returns new instance
*   Module location: `src/allocation/domain/model.py`

Generate the Python code for the [VALUE_OBJECT_NAME] Value Object class.
