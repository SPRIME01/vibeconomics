# Define Domain Entity Class

**Goal:** Generate a new Domain Entity class that represents a core business concept with distinct identity and lifecycle.

**Instructions:**

1.  Create a Python class for the new Entity.
2.  Include an identifier attribute (e.g., UUID or string reference).
3.  Define type-hinted attributes based on the ubiquitous language of the domain.
4.  Implement methods that represent the entity's behavior and business logic.
5.  Include `__eq__` and `__hash__` methods based only on the identity attribute.
6.  Ensure the class follows domain-driven design principles:
    *   Entity equality is based on identity, not structural sameness
    *   Methods should represent meaningful domain behaviors
    *   Use domain language in naming
    *   State can be mutable through defined behaviors
7.  Place the entity class in the appropriate domain module (e.g., `src/allocation/domain/model.py`).

**Context:**

*   Entity name: [ENTITY_NAME] (e.g., Product, Batch)
*   Identity attribute: [ID_ATTRIBUTE] (e.g., reference, sku)
*   Other attributes:
    *   [ATTRIBUTE_1]: [TYPE]
    *   [ATTRIBUTE_2]: [TYPE]
*   Key behaviors:
    *   [METHOD_1]([PARAMS])
    *   [METHOD_2]([PARAMS])
*   Module location: `src/allocation/domain/model.py`

Generate the Python code for the [ENTITY_NAME] entity class.
