import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict, List

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

# Define Pydantic models for our test capability (mirroring from previous A2A test)
class TestA2AInput(BaseModel):
    text_to_process: str
    some_optional_value: int | None = None

class TestA2AOutput(BaseModel):
    processed_text: str
    status_detail: str

# Assumed MCP Manifest URL based on router prefix in nlweb_mcp.py and API_V1_STR
MCP_MANIFEST_ENDPOINT = "/api/v1/tools/mcp" 
TEST_CAPABILITY_NAME = "test_processor" # The A2A capability we expect to find and test

@pytest.mark.asyncio
async def test_nlweb_mcp_interaction_with_a2a_capability():
    """
    Performs an end-to-end test of the NLWeb MCP manifest endpoint and A2A capability integration.
    
    This test registers a mock A2A capability, overrides FastAPI dependencies to use mocked services, fetches the MCP manifest, discovers the test capability, and invokes its endpoint with a test payload. It verifies the manifest structure, capability discovery, endpoint invocation, response correctness, and that the handler service was called with expected arguments. Dependency overrides are cleared after the test.
    """
    
    # 1. Setup Mocks & Dependency Overrides for the 'test_processor' A2A capability
    
    #   a. Mock A2ACapabilityService to ensure 'test_processor' is "registered"
    #      so it can be listed in a hypothetical MCP manifest.
    mock_capability_service = A2ACapabilityService()
    test_capability_metadata = CapabilityMetadata(
        name=TEST_CAPABILITY_NAME,
        description="A test capability for processing text, intended to be exposed via MCP.",
        input_schema=TestA2AInput,
        output_schema=TestA2AOutput,
        handler=None # Handler in CapabilityMetadata is not used by the current A2AHandlerService stub
    )
    mock_capability_service.register_capability(test_capability_metadata)
    app.dependency_overrides[get_a2a_capability_service] = lambda: mock_capability_service

    #   b. Mock A2AHandlerService for the actual execution logic of 'test_processor'
    mock_handler_service = MagicMock(spec=A2AHandlerService)
    input_text_for_mcp_test = "hello mcp a2a"
    expected_handler_output = {
        "processed_text": f"mocked_for_mcp: {input_text_for_mcp_test}",
        "status_detail": "successfully processed by mock A2A handler via MCP call"
    }

    async def mock_handle_a2a_request_for_mcp(capability_name: str, data: BaseModel) -> Dict[str, Any]:
        # This mock will be hit when the A2A endpoint for 'test_processor' is called
        """
        Mocks the handling of an A2A request for the MCP test capability.
        
        Asserts that the provided capability name and input data match the expected test values, then returns a predefined output dictionary.
        
        Args:
            capability_name: The name of the capability being invoked.
            data: The input data for the capability, expected to be an instance of TestA2AInput.
        
        Returns:
            A dictionary representing the expected output of the handler.
        """
        assert capability_name == TEST_CAPABILITY_NAME
        assert isinstance(data, TestA2AInput)
        assert data.text_to_process == input_text_for_mcp_test
        return expected_handler_output
    
    mock_handler_service.handle_a2a_request = AsyncMock(side_effect=mock_handle_a2a_request_for_mcp)
    app.dependency_overrides[get_a2a_handler_service] = lambda: mock_handler_service

    # Initialize TestClient *after* overrides are in place
    client = TestClient(app)

    # 2. Attempt to Fetch and Parse MCP Manifest
    manifest_response = client.get(MCP_MANIFEST_ENDPOINT)
    
    # This assertion will likely fail if the endpoint doesn't exist, which is useful information.
    assert manifest_response.status_code == 200, \
        f"MCP Manifest fetch failed from '{MCP_MANIFEST_ENDPOINT}'. Response: {manifest_response.text}"
    
    manifest = manifest_response.json()
    assert "mcp_version" in manifest, "MCP manifest missing 'mcp_version'"
    # Check for 'tools' or 'a2a_capabilities' or a similar key that would list capabilities
    assert "tools" in manifest or "a2a_capabilities" in manifest or "capabilities" in manifest, \
        "MCP manifest missing a recognizable section for tools/capabilities."

    # 3. Find the 'test_processor' capability in the manifest
    target_capability_details = None
    
    # Iterate through potential structures. A real MCP manifest might have 'tools' with categories,
    # or a flat list like 'a2a_capabilities' or 'capabilities'.
    possible_capability_lists: List[Dict[str, Any]] = []
    if "capabilities" in manifest and isinstance(manifest["capabilities"], list):
        possible_capability_lists.extend(manifest["capabilities"])
    if "a2a_capabilities" in manifest and isinstance(manifest["a2a_capabilities"], list):
        possible_capability_lists.extend(manifest["a2a_capabilities"])
    if "tools" in manifest:
        if isinstance(manifest["tools"], list):
            possible_capability_lists.extend(manifest["tools"])
        elif isinstance(manifest["tools"], dict): # e.g. tools categorized
            for category_tools in manifest["tools"].values():
                if isinstance(category_tools, list):
                    possible_capability_lists.extend(category_tools)

    for cap in possible_capability_lists:
        if cap.get("name") == TEST_CAPABILITY_NAME or cap.get("id") == TEST_CAPABILITY_NAME: # MCP might use 'id'
            target_capability_details = cap
            break
    
    assert target_capability_details is not None, \
        f"Test capability '{TEST_CAPABILITY_NAME}' not found in MCP manifest. Manifest content: {manifest}"
    
    # 4. Extract invocation details
    operation_url = target_capability_details.get("operationUrl")
    http_method = target_capability_details.get("httpMethod", "POST").upper()

    assert operation_url, "operationUrl not found for target capability in MCP manifest"
    # We expect the operationUrl for an A2A capability to point to the A2A execution endpoint
    expected_a2a_op_url_part = f"/a2a/execute/{TEST_CAPABILITY_NAME}"
    assert expected_a2a_op_url_part in operation_url, \
        f"operationUrl '{operation_url}' does not match expected A2A endpoint structure for '{TEST_CAPABILITY_NAME}'."

    # 5. Prepare and Call the Discovered Capability Endpoint
    # The payload should match TestA2AInput, as defined for 'test_processor'
    capability_payload = {
        "text_to_process": input_text_for_mcp_test,
        "some_optional_value": 789 
    }
    
    api_response = None
    if http_method == "POST":
        api_response = client.post(operation_url, json=capability_payload)
    elif http_method == "GET": 
        api_response = client.get(operation_url, params=capability_payload) # GET might not be suitable for complex JSON
    else:
        pytest.fail(f"Unsupported HTTP method '{http_method}' in manifest for test capability.")

    # 6. Assertions for the capability call
    assert api_response is not None
    assert api_response.status_code == 200, f"Capability call to '{operation_url}' failed: {api_response.text}"
    api_response_data = api_response.json()

    # Assert that the response matches TestA2AOutput and mocked data
    assert api_response_data["processed_text"] == f"mocked_mcp_handler: {input_text_for_mcp_test}"
    assert api_response_data["status_detail"] == "successfully processed by mock A2A handler via MCP call"
    
    # Assert that the A2AHandlerService mock was called correctly
    mock_handler_service.handle_a2a_request.assert_called_once()
    # call_args[0] are positional, call_args[1] are keyword
    args_tuple, kwargs_dict = mock_handler_service.handle_a2a_request.call_args
    assert args_tuple[0] == TEST_CAPABILITY_NAME # capability_name
    assert isinstance(args_tuple[1], TestA2AInput) # data (BaseModel instance)
    assert args_tuple[1].text_to_process == input_text_for_mcp_test
    assert args_tuple[1].some_optional_value == 789

    # 7. Clean up dependency overrides
    app.dependency_overrides.clear()
