import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict

from pydantic import BaseModel

# FastAPI app instance
from src.app.entrypoints.fastapi_app import app

# Services and dependencies to be managed/mocked
from src.app.service_layer.a2a_service import (
    A2ACapabilityService,
    A2AHandlerService,
    CapabilityMetadata,
)
from src.app.entrypoints.api.dependencies import (
    get_a2a_capability_service,
    get_a2a_handler_service,
)

# Define Pydantic models for our test capability
class TestA2AInput(BaseModel):
    text_to_process: str
    some_optional_value: int | None = None

class TestA2AOutput(BaseModel):
    processed_text: str
    status_detail: str


TARGET_CAPABILITY_NAME = "test_processor"
A2A_ENDPOINT = f"/api/v1/a2a/execute/{TARGET_CAPABILITY_NAME}"


@pytest.mark.asyncio
async def test_incoming_a2a_capability_execution():
    """
    Tests an incoming A2A capability by:
    1. Registering a mock capability definition.
    2. Mocking the A2AHandlerService to return a predefined response for that capability.
    3. Sending a request to the generic A2A execution endpoint.
    4. Verifying the response and mock interactions.
    """

    # 1. Prepare and register a mock capability
    mock_capability_service = A2ACapabilityService() # Fresh instance for the test
    test_capability = CapabilityMetadata(
        name=TARGET_CAPABILITY_NAME,
        description="A test capability for processing text.",
        input_schema=TestA2AInput,
        output_schema=TestA2AOutput,
        handler=None # Handler in CapabilityMetadata is not used by current A2AHandlerService
    )
    mock_capability_service.register_capability(test_capability)
    
    app.dependency_overrides[get_a2a_capability_service] = lambda: mock_capability_service

    # 2. Mock A2AHandlerService
    mock_handler_service = MagicMock(spec=A2AHandlerService)
    
    input_text_for_test = "hello world for a2a"
    expected_handler_output_dict = {
        "processed_text": f"mocked: {input_text_for_test}",
        "status_detail": "successfully processed by mock"
    }

    async def mock_handle_a2a_request(capability_name: str, data: BaseModel) -> Dict[str, Any]:
        assert capability_name == TARGET_CAPABILITY_NAME
        assert isinstance(data, TestA2AInput)
        assert data.text_to_process == input_text_for_test
        return expected_handler_output_dict

    mock_handler_service.handle_a2a_request = AsyncMock(side_effect=mock_handle_a2a_request)
    app.dependency_overrides[get_a2a_handler_service] = lambda: mock_handler_service
    
    # Initialize client *after* all overrides are set
    client = TestClient(app)

    # 3. Prepare A2A request payload
    a2a_request_payload = {
        "text_to_process": input_text_for_test,
        "some_optional_value": 123
    }

    # 4. Make the call to the A2A endpoint
    response = client.post(A2A_ENDPOINT, json=a2a_request_payload)

    # 5. Assertions
    assert response.status_code == 200, f"Response content: {response.text}"
    response_data = response.json()

    # Assert response structure and content (matches TestA2AOutput)
    assert response_data["processed_text"] == f"mocked: {input_text_for_test}"
    assert response_data["status_detail"] == "successfully processed by mock"
    
    # Assert that the mocked handler was called
    mock_handler_service.handle_a2a_request.assert_called_once()
    call_args = mock_handler_service.handle_a2a_request.call_args[0] # Get positional args
    assert call_args[0] == TARGET_CAPABILITY_NAME
    assert isinstance(call_args[1], TestA2AInput)
    assert call_args[1].text_to_process == input_text_for_test
    assert call_args[1].some_optional_value == 123

    # 6. Clean up dependency overrides
    app.dependency_overrides.clear()
