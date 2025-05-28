import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import Type

# Assume these modules exist and will be created later
# from app.entrypoints.api.routes.a2a_api import a2a_api_router 
from app.entrypoints.api.routes.a2a_api import a2a_api_router # Actual router
from app.service_layer.a2a_service import A2ACapabilityService, CapabilityMetadata, A2AHandlerService # Actual A2AHandlerService
from app.domain.a2a.models import SummarizeTextA2ARequest, SummarizeTextA2AResponse


@pytest.fixture
def mock_a2a_capability_service() -> AsyncMock:
    """
    Creates a mocked A2ACapabilityService with a predefined "SummarizeText" capability.
    
    The returned mock service's get_capability method returns a CapabilityMetadata instance
    for "SummarizeText" with associated request and response schemas and a mocked handler.
    """
    mock_service = AsyncMock(spec=A2ACapabilityService)
    
    # Define a sample CapabilityMetadata for "SummarizeText"
    summarize_text_capability = CapabilityMetadata(
        name="SummarizeText",
        description="Summarizes a given text.",
        input_schema=SummarizeTextA2ARequest,
        output_schema=SummarizeTextA2AResponse,
        handler=AsyncMock() # Mock handler for the capability itself
    )
    
    mock_service.get_capability = MagicMock(return_value=summarize_text_capability)
    return mock_service


@pytest.fixture
def mock_a2a_handler_service() -> AsyncMock:
    # Use the actual A2AHandlerService for spec
    """
    Creates an AsyncMock of A2AHandlerService with a mocked handle_a2a_request method returning a fixed SummarizeTextA2AResponse instance.
    
    Returns:
        An AsyncMock instance of A2AHandlerService with handle_a2a_request preconfigured for testing.
    """
    mock_service = AsyncMock(spec=A2AHandlerService) 
    # The actual router expects the handler_service to return a Pydantic model or a dict
    # that can be parsed by capability.output_schema.
    # If SummarizeTextA2AResponse is returned, it's already a model.
    mock_service.handle_a2a_request = AsyncMock(return_value=SummarizeTextA2AResponse(summary="Mocked summary"))
    return mock_service


@pytest.fixture
def test_app(
    mock_a2a_capability_service: AsyncMock, 
    mock_a2a_handler_service: AsyncMock 
) -> FastAPI:
    """
    Creates a FastAPI application instance with the A2A API router and overrides service dependencies with provided mocks.
    
    Args:
        mock_a2a_capability_service: Mocked capability service to inject into the app.
        mock_a2a_handler_service: Mocked handler service to inject into the app.
    
    Returns:
        A FastAPI app configured for testing with dependency overrides.
    """
    app = FastAPI()
    
    # Use the actual imported router
    app.include_router(a2a_api_router, prefix="/a2a")
    
    # Dependency overrides for the actual services used by the imported router
    # The keys for dependency_overrides should be the actual service classes.
    # Assuming the actual router uses A2ACapabilityService and A2AHandlerService via Depends()
    app.dependency_overrides[A2ACapabilityService] = lambda: mock_a2a_capability_service
    app.dependency_overrides[A2AHandlerService] = lambda: mock_a2a_handler_service
    
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """
    Provides a TestClient instance for the given FastAPI application.
    
    Used to simulate HTTP requests in tests.
    """
    return TestClient(test_app)


def test_execute_summarize_text_capability(
    client: TestClient, 
    mock_a2a_capability_service: AsyncMock, 
    mock_a2a_handler_service: AsyncMock # Changed parameter
):
    """
    Tests successful execution of the 'SummarizeText' capability via the A2A API.
    
    Sends a valid request to the '/a2a/execute/SummarizeText' endpoint and verifies
    that the response contains the expected summary. Asserts that the capability and
    handler services are called with the correct arguments, including proper parsing
    of the request data into the expected Pydantic model.
    """
    payload = {"text_to_summarize": "This is a test."}
    # Correct way to pass request body for a Pydantic model in TestClient
    # The placeholder endpoint doesn't dynamically use SummarizeTextA2ARequest,
    # so we send a dict. FastAPI will try to match it.
    response = client.post("/a2a/execute/SummarizeText", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"summary": "Mocked summary"}
    
    mock_a2a_capability_service.get_capability.assert_called_once_with("SummarizeText")
    
    # Assert that the handler service was called correctly
    # We need to ensure the call_args match what the endpoint would send
    mock_a2a_handler_service.handle_a2a_request.assert_called_once()
    call_args = mock_a2a_handler_service.handle_a2a_request.call_args
    assert call_args[1]['capability_name'] == "SummarizeText"
    
    # The 'data' argument in the mock call will be an instance of SummarizeTextA2ARequest
    # because the actual router parses the request_data using capability.input_schema.
    assert isinstance(call_args[1]['data'], SummarizeTextA2ARequest)
    assert call_args[1]['data'].text_to_summarize == "This is a test."

    # The actual router's handle_a2a_request call does not pass 'capability_metadata'.
    # It passes 'capability_name' and 'data'.
    # So, this assertion needs to be removed or changed if we adapt the mock call.
    # For now, let's assume the mock_a2a_handler_service.handle_a2a_request was called with:
    # (capability_name="SummarizeText", data=SummarizeTextA2ARequest(text_to_summarize="This is a test."))
    # The capability_metadata is not passed to handler_service.handle_a2a_request in the actual router.
    # assert call_args[1]['capability_metadata'].name == "SummarizeText" # This will fail.


def test_execute_capability_not_found(client: TestClient, mock_a2a_capability_service: AsyncMock):
    # Configure the mock to return None for "UnknownCapability"
    """
    Tests that executing an unknown capability returns a 404 response with an appropriate error message.
    
    Verifies that the capability service is queried with the unknown capability name and that the API responds with a not found error when the capability does not exist.
    """
    mock_a2a_capability_service.get_capability.return_value = None
    
    response = client.post("/a2a/execute/UnknownCapability", json={"data": "some data"})
    
    assert response.status_code == 404
    # The actual router returns f"Capability '{capability_name}' not found"
    assert response.json() == {"detail": "Capability 'UnknownCapability' not found"}
    mock_a2a_capability_service.get_capability.assert_called_with("UnknownCapability")


def test_execute_capability_invalid_input(client: TestClient, mock_a2a_capability_service: AsyncMock):
    # Get the valid capability metadata for SummarizeText
    """
    Tests that the API returns a 422 error with validation details when input data for a capability is invalid.
    
    Sends a POST request to execute the "SummarizeText" capability with a malformed payload, then asserts that the response contains Pydantic validation errors for missing required fields.
    """
    summarize_text_capability = CapabilityMetadata(
        name="SummarizeText",
        description="Summarizes a given text.",
        input_schema=SummarizeTextA2ARequest, # Actual input schema
        output_schema=SummarizeTextA2AResponse,
        handler=AsyncMock() # Placeholder handler
    )
    mock_a2a_capability_service.get_capability.return_value = summarize_text_capability
    
    # Make a POST request with invalid JSON payload (missing 'text_to_summarize')
    # The actual router will perform Pydantic validation.
    response = client.post("/a2a/execute/SummarizeText", json={"wrong_field": "This is a test."})
    
    assert response.status_code == 422
    
    # Pydantic's ValidationError e.errors() returns a list of error objects.
    # Example: [{'type': 'missing', 'loc': ('text_to_summarize',), 'msg': 'Field required', ...}]
    response_json = response.json()
    assert "detail" in response_json
    assert isinstance(response_json["detail"], list)
    assert len(response_json["detail"]) > 0
    assert response_json["detail"][0]["type"] == "missing"
    assert response_json["detail"][0]["loc"] == ["text_to_summarize"]
    
    mock_a2a_capability_service.get_capability.assert_called_with("SummarizeText")

# No longer need the local "Depends" placeholder if not used elsewhere explicitly
# from fastapi import Depends 
