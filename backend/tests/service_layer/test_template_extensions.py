import json # Added
from unittest.mock import Mock

from app.adapters.activepieces_adapter import ActivePiecesAdapter # Added
from app.adapters.mem0_adapter import MemorySearchResult
from app.service_layer.memory_service import MemoryService # Keep if TemplateService requires it, or remove if None is fine
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
    input_data: dict[str, any] = {"param1": "value1", "param2": 100}
    # In the template, the input data must be a single string.
    # If it's JSON, it needs to be a JSON string.
    # The `process_template_extensions` in TemplateExtensionRegistry splits args by ':',
    # so complex JSON strings with internal colons might be an issue if not handled carefully.
    # For this test, assume input_data_str is a well-formed JSON string passed as a single argument segment.
    # The current parser in TemplateExtensionRegistry (based on the problem description)
    # uses `args = [arg.strip() for arg in args_str.split(":")]`.
    # This implies the JSON string itself should not contain colons, or the parsing logic
    # for arguments needs to be robust enough (e.g. knowing the last arg is a JSON blob).
    # For simplicity, we'll assume the JSON string is simple or the parsing logic is robust.
    # Given the `activepieces_run_workflow` expects `input_data_str`, this is what we pass in the template.
    input_data_json_str = json.dumps(input_data)

    expected_workflow_result_dict: dict[str, any] = {
        "status": "completed",
        "output_data": {"result": "all good"},
    }
    mock_activepieces_adapter.run_workflow.return_value = (
        expected_workflow_result_dict
    )

    # Instantiate TemplateService with the mock ActivePiecesAdapter
    # Pass None for memory_service if not relevant for this specific test.
    template_service = TemplateService(
        activepieces_adapter=mock_activepieces_adapter, memory_service=None
    )

    # Construct the template content string
    # The args_str is split by ':', so workflow_id is args[0], input_data_json_str is args[1]
    # for the `activepieces_run_workflow` function if called via the registry's simple split.
    # The bound function `bound_activepieces_run_workflow` expects (workflow_id: str, input_data_str: str)
    template_content = (
        f"Output: {{activepieces:run_workflow:{expected_workflow_id}:{input_data_json_str}}}"
    )

    # The expected output string
    expected_output_str = f"Output: {json.dumps(expected_workflow_result_dict)}"

    # Act
    result: str = template_service.process_template(template_content)

    # Assert
    # The bound function `bound_activepieces_run_workflow` calls the actual
    # `activepieces_run_workflow` which then calls `mock_activepieces_adapter.run_workflow`
    # The `activepieces_run_workflow` function parses the JSON string.
    mock_activepieces_adapter.run_workflow.assert_called_once_with(
        workflow_id=expected_workflow_id, input_data=input_data
    )
    assert result == expected_output_str
    assert isinstance(result, str)
