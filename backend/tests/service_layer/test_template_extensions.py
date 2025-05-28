import json
from typing import Any
from unittest.mock import Mock

from app.adapters.activepieces_adapter import ActivePiecesAdapter
from app.adapters.mem0_adapter import MemorySearchResult
from app.service_layer.memory_service import MemoryService
from app.service_layer.template_extensions import (
    TemplateExtensionRegistry,
    create_a2a_extensions, # Import the new factory
    ExtensionArgumentError, # Import custom error
    GenericRequestData, # Import GenericRequestData if it's moved to main file, or define locally
)
from app.service_layer.template_service import TemplateService
from app.adapters.a2a_client_adapter import A2AClientAdapter # For mocking
from unittest.mock import AsyncMock # For async mocks
import pytest # For async tests and fixtures
from pydantic import BaseModel, ConfigDict # For local GenericRequestData if not imported


def test_memory_template_extension() -> None:
    """
    Tests that TemplateService correctly processes the memory:search extension by replacing the placeholder with formatted search results from the mocked MemoryService.
    """
    # Arrange
    mock_memory_service = Mock(spec=MemoryService)
    mock_search_results: list[MemorySearchResult] = [
        MemorySearchResult(
            id="mem1",
            content="User prefers morning meetings",
            score=0.95,
            metadata=None,
        ),
        MemorySearchResult(
            id="mem2",
            content="User is in EST timezone",
            score=0.87,
            metadata=None,
        ),
    ]
    mock_memory_service.search.return_value = mock_search_results

    template_service = TemplateService(memory_service=mock_memory_service)

    template_content = (
        "Based on your preferences: {{memory:search:user123:meeting preferences}}"
    )
    expected_user_id = "user123"
    expected_query = "meeting preferences"
    expected_output = (
        "Based on your preferences: 1. User prefers morning meetings (relevance: 0.95)\n"
        "2. User is in EST timezone (relevance: 0.87)"
    )

    # Act
    result = template_service.process_template(template_content)

    # Assert
    mock_memory_service.search.assert_called_once_with(
        user_id=expected_user_id, query=expected_query, limit=5
    )
    assert result == expected_output
    assert isinstance(result, str)


def test_activepieces_extension() -> None:
    """Test that TemplateService processes activepieces:run_workflow extension correctly."""
    # Arrange
    mock_activepieces_adapter = Mock(spec=ActivePiecesAdapter)
    expected_workflow_id = "wf_123"
    input_data: dict[str, Any] = {"param1": "value1", "param2": 100}
    input_data_json_str = json.dumps(input_data)

    expected_workflow_result_dict: dict[str, Any] = {
        "status": "completed",
        "output_data": {"result": "all good"},
    }
    mock_activepieces_adapter.run_workflow.return_value = expected_workflow_result_dict

    template_service = TemplateService(
        activepieces_adapter=mock_activepieces_adapter, memory_service=None
    )

    template_content = f"Output: {{{{activepieces:run_workflow:{expected_workflow_id}:{input_data_json_str}}}}}"
    expected_output_str = f"Output: {json.dumps(expected_workflow_result_dict)}"

    # Act
    result: str = template_service.process_template(template_content)

    # Assert - First check that the extension was processed (template placeholder was replaced)
    assert "{{activepieces:run_workflow" not in result, (
        f"Extension was not processed. Result: {result}"
    )

    # Then check that the adapter was called correctly
    mock_activepieces_adapter.run_workflow.assert_called_once()
    call_args = mock_activepieces_adapter.run_workflow.call_args
    assert call_args.kwargs["workflow_id"] == expected_workflow_id
    assert call_args.kwargs["input_data"] == input_data

    # Finally check the output
    assert result == expected_output_str
    assert isinstance(result, str)


def test_activepieces_extension_invalid_json() -> None:
    """Test that TemplateService returns error for invalid JSON input and does not call adapter."""
    mock_activepieces_adapter = Mock(spec=ActivePiecesAdapter)
    template_service = TemplateService(
        activepieces_adapter=mock_activepieces_adapter, memory_service=None
    )
    workflow_id = "wf_456"
    invalid_json_str = '{"param1": "value1", "param2": 100'  # Missing closing }

    template_content = (
        f"Result: {{{{activepieces:run_workflow:{workflow_id}:{invalid_json_str}}}}}"
    )

    # Act
    result = template_service.process_template(template_content)

    # Assert - First check that the extension was processed
    assert "{{activepieces:run_workflow" not in result, (
        f"Extension was not processed. Result: {result}"
    )

    # Then check for error indicators
    assert "Invalid JSON input" in result or "error" in result or "ERROR" in result, (
        f"No error found in result: {result}"
    )

    # Finally ensure adapter was not called
    mock_activepieces_adapter.run_workflow.assert_not_called()


def test_debug_extension_parsing() -> None:
    """Debug test to understand extension parsing."""
    mock_activepieces_adapter = Mock(spec=ActivePiecesAdapter)
    mock_activepieces_adapter.run_workflow.return_value = {"test": "result"}

    template_service = TemplateService(
        activepieces_adapter=mock_activepieces_adapter, memory_service=None
    )

    # Check what extensions are registered
    print(
        f"Registered extensions: {list(template_service.extension_registry._extensions.keys())}"
    )

    # Test boundary finding directly
    registry = template_service.extension_registry
    test_template = '{{activepieces:run_workflow:test_id:{"key":"value"}}}'
    boundaries = registry._find_extension_boundaries(test_template)
    print(f"Found boundaries: {boundaries}")

    # Check if the extension function exists
    if boundaries:
        start_pos, end_pos, namespace, operation, args_str = boundaries[0]
        extension_name = f"{namespace}_{operation}"
        print(f"Looking for extension: {extension_name}")
        print(f"Extension exists: {extension_name in registry._extensions}")

        if extension_name in registry._extensions:
            extension_func = registry._extensions[extension_name]
            print(f"Extension function: {extension_func}")

            # Try calling it directly
            try:
                if ":" in args_str:
                    workflow_id, input_data_str = args_str.split(":", 1)
                    result = extension_func(workflow_id.strip(), input_data_str.strip())
                    print(f"Direct call result: {result}")
                else:
                    result = extension_func(args_str.strip(), "{}")
                    print(f"Direct call result (no args): {result}")
            except Exception as e:
                print(f"Direct call error: {e}")
                import traceback

                traceback.print_exc()
    else:
        print("No boundaries found!")

    # Test with different template formats
    templates_to_test = [
        "{{activepieces:run_workflow:test_id:{}}}",
        '{{activepieces:run_workflow:test_id:{"key":"value"}}}',
        "{{activepieces_run_workflow:test_id:{}}}",  # Try underscore format
    ]

    for template in templates_to_test:
        print(f"\nTesting template: {template}")
        result = template_service.process_template(template)
        print(f"Result: {result}")


# Add test to verify boundary detection
def test_boundary_detection() -> None:
    """
    Tests that the TemplateExtensionRegistry correctly identifies extension boundaries and parses namespace, operation, and arguments from template strings.
    """
    registry = TemplateExtensionRegistry()

    # Test simple case
    simple = "{{memory:search:user123:query text}}"
    boundaries = registry._find_extension_boundaries(simple)
    assert len(boundaries) == 1
    start, end, namespace, operation, args = boundaries[0]
    assert namespace == "memory"
    assert operation == "search"
    assert args == "user123:query text"

    # Test with JSON
    json_template = (
        '{{activepieces:run_workflow:wf_123:{"param1":"value1","param2":100}}}'
    )
    boundaries = registry._find_extension_boundaries(json_template)
    assert len(boundaries) == 1
    start, end, namespace, operation, args = boundaries[0]
    assert namespace == "activepieces"
    assert operation == "run_workflow"
    assert args == 'wf_123:{"param1":"value1","param2":100}'


# --- Tests for A2A Invoke Extension ---

@pytest.fixture
def mock_a2a_client_adapter_fixture() -> AsyncMock:
    """
    Provides an asynchronous mock instance of the A2AClientAdapter for testing purposes.
    
    Returns:
        An AsyncMock object configured to mimic the A2AClientAdapter interface.
    """
    return AsyncMock(spec=A2AClientAdapter)

# If GenericRequestData is not globally available from template_extensions.py, define it here for tests
# class GenericRequestData(BaseModel):
# model_config = ConfigDict(extra='allow')


@pytest.mark.asyncio
async def test_a2a_invoke_extension_success(mock_a2a_client_adapter_fixture: AsyncMock):
    # Arrange
    """
    Tests that the 'a2a_invoke' template extension correctly parses arguments, calls the adapter
    with the expected parameters, and returns the adapter's response.
    
    Verifies that the extension function wraps the payload in a GenericRequestData model and
    invokes the adapter's 'execute_remote_capability' method with the correct agent URL,
    capability name, and payload. Asserts that the returned result matches the expected response.
    """
    registry = TemplateExtensionRegistry()
    a2a_extensions = create_a2a_extensions(mock_a2a_client_adapter_fixture)
    registry.register("a2a_invoke", a2a_extensions["a2a_invoke"])

    agent_url = "http://fakeagent.com"
    capability_name = "summarize"
    payload_dict = {"text": "long text to summarize"}
    payload_json_str = json.dumps(payload_dict)
    
    gpt_args_str = f"agent_url={agent_url}:capability={capability_name}:payload={payload_json_str}"
    
    expected_response_data = {"summary": "This is a summary."}
    mock_a2a_client_adapter_fixture.execute_remote_capability.return_value = expected_response_data
    
    # Act
    extension_function = registry.get("a2a_invoke")
    assert extension_function is not None
    
    result = await extension_function(gpt_args_str)
    
    # Assert
    # Verify the adapter was called correctly
    # The payload should be wrapped in GenericRequestData by the extension
    # Or, if GenericRequestData is not used, it would be payload_dict directly.
    # Based on the current _a2a_invoke_extension_async, it uses GenericRequestData.
    
    # Create the expected Pydantic model instance that the adapter should receive
    # This requires GenericRequestData to be defined/imported.
    # Assuming GenericRequestData is defined as in template_extensions.py
    from app.service_layer.template_extensions import GenericRequestData as ActualGenericRequestData
    expected_request_payload = ActualGenericRequestData(**payload_dict)

    mock_a2a_client_adapter_fixture.execute_remote_capability.assert_called_once_with(
        agent_url=agent_url,
        capability_name=capability_name,
        request_payload=expected_request_payload, # Check if this matches
        response_model=None
    )
    
    assert result == expected_response_data


@pytest.mark.asyncio
async def test_a2a_invoke_extension_parsing_errors(mock_a2a_client_adapter_fixture: AsyncMock):
    # Arrange
    """
    Tests that the a2a_invoke extension raises ExtensionArgumentError for missing or invalid arguments.
    
    Verifies that the extension function detects and reports missing 'agent_url', missing 'capability', and invalid JSON in the 'payload' argument, raising ExtensionArgumentError with appropriate messages.
    """
    registry = TemplateExtensionRegistry()
    a2a_extensions = create_a2a_extensions(mock_a2a_client_adapter_fixture)
    registry.register("a2a_invoke", a2a_extensions["a2a_invoke"])
    extension_function = registry.get("a2a_invoke")
    assert extension_function is not None

    # Test missing agent_url
    bad_args_missing_agent_url = "capability=summarize:payload={}"
    with pytest.raises(ExtensionArgumentError, match="Missing 'agent_url'"):
        await extension_function(bad_args_missing_agent_url)

    # Test missing capability
    bad_args_missing_capability = "agent_url=http://fake.com:payload={}"
    with pytest.raises(ExtensionArgumentError, match="Missing 'capability'"):
        await extension_function(bad_args_missing_capability)

    # Test invalid JSON payload
    bad_args_invalid_json = "agent_url=http://fake.com:capability=summarize:payload=not_json"
    with pytest.raises(ExtensionArgumentError, match="Invalid JSON payload"):
        await extension_function(bad_args_invalid_json)


@pytest.mark.asyncio
async def test_a2a_invoke_extension_adapter_error(mock_a2a_client_adapter_fixture: AsyncMock):
    # Arrange
    """
    Tests that the a2a_invoke extension propagates exceptions raised by the adapter.
    
    Verifies that if the underlying A2A client adapter raises a RuntimeError during
    remote capability execution, the extension function raises the same error.
    """
    registry = TemplateExtensionRegistry()
    a2a_extensions = create_a2a_extensions(mock_a2a_client_adapter_fixture)
    registry.register("a2a_invoke", a2a_extensions["a2a_invoke"])
    extension_function = registry.get("a2a_invoke")
    assert extension_function is not None

    agent_url = "http://fakeagent.com"
    capability_name = "summarize"
    payload_dict = {"text": "long text"}
    payload_json_str = json.dumps(payload_dict)
    gpt_args_str = f"agent_url={agent_url}:capability={capability_name}:payload={payload_json_str}"

    # Simulate an error from the adapter
    mock_a2a_client_adapter_fixture.execute_remote_capability.side_effect = RuntimeError("Adapter network error")

    with pytest.raises(RuntimeError, match="Adapter network error"):
        await extension_function(gpt_args_str)
