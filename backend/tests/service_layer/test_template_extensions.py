import json
from typing import Any
from unittest.mock import Mock

from app.adapters.activepieces_adapter import ActivePiecesAdapter
from app.adapters.mem0_adapter import MemorySearchResult
from app.service_layer.memory_service import MemoryService
from app.service_layer.template_extensions import (
    TemplateExtensionRegistry,  # Add this import
)
from app.service_layer.template_service import TemplateService


def test_memory_template_extension() -> None:
    """Test that TemplateService processes memory:search extension correctly."""
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
    """Test the boundary detection specifically."""
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
