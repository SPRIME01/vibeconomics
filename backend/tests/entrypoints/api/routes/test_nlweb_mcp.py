from typing import Any
from unittest.mock import (  # Keep patch if other lower-level mocks are needed
    AsyncMock,
    Mock,
)

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the original dependency function to use as a key for overriding
from app.entrypoints.api.routes.nlweb_mcp import (
    get_ai_pattern_execution_service,
    router,
)


@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI app instance for testing."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app)


def test_nlweb_ask_endpoint(
    client: TestClient, app: FastAPI
):  # Add app fixture to test
    """Test that the /nlweb/ask endpoint correctly calls AIPatternExecutionService."""
    # Arrange
    mock_service_instance = Mock()  # This will be our AIPatternExecutionService mock
    mock_service_instance.execute_pattern = AsyncMock(
        return_value={
            "query_id": "test-query-123",
            "results": [
                {
                    "url": "https://example.com/doc1",
                    "name": "Test Document 1",
                    "site": "test-site",
                    "score": 0.95,
                    "description": "A test document for validation",
                    "schema_object": {"id": "doc1", "type": "document"},
                }
            ],
        }
    )

    test_query: str = "What is the economic impact of renewable energy?"
    expected_input_variables: dict[str, Any] = {
        "query": test_query,
        "site": "economics-site",
        "mode": "list",
        "streaming": True,
    }

    # Override the dependency using app.dependency_overrides
    # The key is the original dependency function imported from the route's module
    app.dependency_overrides[get_ai_pattern_execution_service] = (
        lambda: mock_service_instance
    )

    # With dependency_overrides, the patches for PatternService.get_pattern_content
    # and TemplateService.render are not strictly needed here because the real
    # get_ai_pattern_execution_service (which creates those services) won't be called.
    # The mock_service_instance.execute_pattern is an AsyncMock and won't execute real logic.

    response = client.post(
        "/tools/nlweb/ask",
        json={
            "query": test_query,
            "site": "economics-site",
            "mode": "list",
            "streaming": True,
        },
    )

    # Assert service was called with correct pattern and variables
    mock_service_instance.execute_pattern.assert_called_once_with(
        pattern_name="nlweb_ask_query",
        input_variables=expected_input_variables,
        session_id=None,  # query_id was not provided in request
    )

    # Assert response structure
    assert response.status_code == 200
    response_data = response.json()
    assert "query_id" in response_data
    assert "results" in response_data
    assert len(response_data["results"]) > 0

    # Verify result structure matches API spec
    result = response_data["results"][0]
    assert "url" in result
    assert "name" in result
    assert "site" in result
    assert "score" in result
    assert "description" in result
    assert "schema_object" in result

    # Clean up the override to not affect other tests
    del app.dependency_overrides[get_ai_pattern_execution_service]
