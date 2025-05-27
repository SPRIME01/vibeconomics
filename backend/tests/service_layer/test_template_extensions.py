from unittest.mock import Mock

from app.adapters.mem0_adapter import MemorySearchResult
from app.service_layer.memory_service import MemoryService
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
