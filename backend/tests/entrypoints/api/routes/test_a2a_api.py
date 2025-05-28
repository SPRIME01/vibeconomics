from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.entrypoints.api.dependencies import (
    get_a2a_capability_service,
    get_a2a_handler_service,
)
from app.entrypoints.api.routes.a2a_api import a2a_api_router
from app.service_layer.a2a_service import (
    A2ACapabilityService,
    A2AHandlerService,
    CapabilityMetadata,
)


class MockRequest(BaseModel):
    message: str


class MockResponse(BaseModel):
    summary: str


@pytest.fixture
def mock_a2a_capability_service():
    """Mock A2A capability service."""
    service = Mock(spec=A2ACapabilityService)

    # Create a test capability
    capability = CapabilityMetadata(
        name="test_capability",
        description="Test capability",
        input_schema=MockRequest,
        output_schema=MockResponse,
    )

    service.get_capability.return_value = capability
    return service


@pytest.fixture
def mock_a2a_handler_service():
    """Mock A2A handler service."""
    service = Mock(spec=A2AHandlerService)
    service.handle_a2a_request = AsyncMock(return_value={"summary": "Test summary"})
    return service


@pytest.fixture
def test_app(mock_a2a_capability_service, mock_a2a_handler_service):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(a2a_api_router, prefix="/a2a")

    # Override dependencies
    app.dependency_overrides[get_a2a_capability_service] = (
        lambda: mock_a2a_capability_service
    )
    app.dependency_overrides[get_a2a_handler_service] = lambda: mock_a2a_handler_service

    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


def test_execute_capability_success(
    client, mock_a2a_capability_service, mock_a2a_handler_service
):
    """Test successful capability execution."""
    # Arrange
    request_data = {"message": "test message"}

    # Act
    response = client.post("/a2a/execute/test_capability", json=request_data)

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result == {"summary": "Test summary"}

    # Verify service calls
    mock_a2a_capability_service.get_capability.assert_called_once_with(
        "test_capability"
    )
    mock_a2a_handler_service.handle_a2a_request.assert_called_once()


def test_execute_capability_not_found(client, mock_a2a_capability_service):
    """Test capability not found error."""
    # Arrange
    mock_a2a_capability_service.get_capability.return_value = None
    request_data = {"message": "test message"}

    # Act
    response = client.post("/a2a/execute/nonexistent_capability", json=request_data)

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_execute_capability_invalid_input(client, mock_a2a_capability_service):
    """Test invalid input validation."""
    # Arrange
    request_data = {"invalid_field": "test"}  # Missing required 'message' field

    # Act
    response = client.post("/a2a/execute/test_capability", json=request_data)

    # Assert
    assert response.status_code == 422
    assert "detail" in response.json()


def test_execute_capability_missing_input_schema(client, mock_a2a_capability_service):
    """Test capability with missing input schema."""
    # Arrange
    capability = CapabilityMetadata(
        name="test_capability",
        description="Test capability",
        input_schema=None,  # Missing input schema
        output_schema=MockResponse,
    )
    mock_a2a_capability_service.get_capability.return_value = capability
    request_data = {"message": "test message"}

    # Act
    response = client.post("/a2a/execute/test_capability", json=request_data)

    # Assert
    assert response.status_code == 500
    assert "Input schema not defined" in response.json()["detail"]


def test_execute_capability_missing_output_schema(client, mock_a2a_capability_service):
    """Test capability with missing output schema."""
    # Arrange
    capability = CapabilityMetadata(
        name="test_capability",
        description="Test capability",
        input_schema=MockRequest,
        output_schema=None,  # Missing output schema
    )
    mock_a2a_capability_service.get_capability.return_value = capability
    request_data = {"message": "test message"}

    # Act
    response = client.post("/a2a/execute/test_capability", json=request_data)

    # Assert
    assert response.status_code == 500
    assert "Output schema not defined" in response.json()["detail"]
