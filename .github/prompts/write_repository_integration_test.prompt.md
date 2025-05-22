# Write Repository Integration Test

**Goal:** Generate an integration test that verifies a concrete Repository implementation correctly interacts with its underlying infrastructure.

**Instructions:**

1.  Create a pytest test function in the appropriate test module.
2.  Set up the required infrastructure components:
    *   Database connection/session
    *   ORM configuration if needed
    *   Concrete Repository instance
3.  Create test domain model objects with known test data.
4.  Exercise the repository's methods (add, get, list).
5.  Verify results by directly querying the persistence layer.
6.  Implement proper test cleanup:
    *   Use pytest fixtures where appropriate
    *   Clean up test data after each test
    *   Consider transaction rollback patterns
7.  Follow integration testing best practices:
    *   Test with real infrastructure
    *   Verify actual persistence
    *   Check error cases and edge conditions
    *   Use meaningful test data
    *   Keep tests independent and isolated

**Context:**

*   Repository class: `[REPO_CLASS]` (e.g., SqlAlchemyProductRepository)
*   Domain model: `[MODEL_CLASS]` (e.g., Product)
*   Test scenarios:
    *   `[SCENARIO_1]` (e.g., "add and retrieve a product")
    *   `[SCENARIO_2]` (e.g., "list all products")
    *   `[SCENARIO_3]` (e.g., "handle missing product")
*   Verification approach:
    *   `[VERIFY_METHOD]` (e.g., "direct SQL query", "ORM session")
*   Module location: `tests/integration/test_repository.py`

Generate the Python code for the repository integration test.
