from unittest.mock import Mock
from typing import List
import pytest

from app.service_layer.query_handlers.memory_query_handlers import SearchMemoryQueryHandler
from app.domain.memory.queries import SearchMemoryQuery
from app.domain.memory.models import MemoryQueryResult
from app.infrastructure.memory.repository import AbstractMemoryRepository


class TestSearchMemoryQueryHandler:
    """Test suite for SearchMemoryQueryHandler following query handler patterns."""

    @pytest.fixture
    def mock_memory_repository(self) -> Mock:
        """Mock memory repository following AbstractMemoryRepository interface."""
        repo = Mock(spec=AbstractMemoryRepository)
        return repo

    @pytest.fixture
    def handler(self, mock_memory_repository: Mock) -> SearchMemoryQueryHandler:
        """Create handler instance with mocked repository."""
        return SearchMemoryQueryHandler(repository=mock_memory_repository)

    @pytest.fixture
    def search_memory_query(self) -> SearchMemoryQuery:
        """Create a sample search memory query."""
        return SearchMemoryQuery(
            user_id="user123",
            query_text="test query",
            limit=10,
            filters={"category": "work"}
        )

    @pytest.fixture
    def sample_query_results(self) -> List[MemoryQueryResult]:
        """Create sample query results for testing."""
        return [
            MemoryQueryResult(
                memory_id="mem1",
                user_id="user123",
                content="First test memory",
                metadata={"category": "work"},
                relevance_score=0.95
            ),
            MemoryQueryResult(
                memory_id="mem2",
                user_id="user123",
                content="Second test memory",
                metadata={"category": "work"},
                relevance_score=0.87
            )
        ]

    def test_handler_calls_repository_search_method(
        self,
        handler: SearchMemoryQueryHandler,
        search_memory_query: SearchMemoryQuery,
        mock_memory_repository: Mock,
        sample_query_results: List[MemoryQueryResult]
    ) -> None:
        """Test that handler correctly calls repository's search method."""
        # Arrange
        mock_memory_repository.search.return_value = sample_query_results

        # Act
        result = handler.handle(search_memory_query)

        # Assert
        mock_memory_repository.search.assert_called_once_with(
            user_id=search_memory_query.user_id,
            query_text=search_memory_query.query_text,
            limit=search_memory_query.limit,
            filters=search_memory_query.filters
        )

    def test_handler_returns_memory_query_results(
        self,
        handler: SearchMemoryQueryHandler,
        search_memory_query: SearchMemoryQuery,
        mock_memory_repository: Mock,
        sample_query_results: List[MemoryQueryResult]
    ) -> None:
        """Test that handler returns correct MemoryQueryResult objects."""
        # Arrange
        mock_memory_repository.search.return_value = sample_query_results

        # Act
        result = handler.handle(search_memory_query)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2

        # Verify first result
        first_result = result[0]
        assert isinstance(first_result, MemoryQueryResult)
        assert first_result.memory_id == "mem1"
        assert first_result.user_id == "user123"
        assert first_result.content == "First test memory"
        assert first_result.metadata == {"category": "work"}
        assert first_result.relevance_score == 0.95

        # Verify second result
        second_result = result[1]
        assert isinstance(second_result, MemoryQueryResult)
        assert second_result.memory_id == "mem2"
        assert second_result.relevance_score == 0.87

    def test_handler_returns_empty_list_when_no_results(
        self,
        handler: SearchMemoryQueryHandler,
        search_memory_query: SearchMemoryQuery,
        mock_memory_repository: Mock
    ) -> None:
        """Test that handler returns empty list when no memories found."""
        # Arrange
        mock_memory_repository.search.return_value = []

        # Act
        result = handler.handle(search_memory_query)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_handler_with_minimal_query_parameters(
        self,
        handler: SearchMemoryQueryHandler,
        mock_memory_repository: Mock
    ) -> None:
        """Test handler with minimal query parameters."""
        # Arrange
        minimal_query = SearchMemoryQuery(
            user_id="user123",
            query_text="minimal query"
        )
        mock_memory_repository.search.return_value = []

        # Act
        handler.handle(minimal_query)

        # Assert
        mock_memory_repository.search.assert_called_once_with(
            user_id="user123",
            query_text="minimal query",
            limit=None,
            filters=None
        )

    def test_handler_propagates_repository_exceptions(
        self,
        handler: SearchMemoryQueryHandler,
        search_memory_query: SearchMemoryQuery,
        mock_memory_repository: Mock
    ) -> None:
        """Test that handler properly propagates repository exceptions."""
        # Arrange
        mock_memory_repository.search.side_effect = Exception("Search service unavailable")

        # Act & Assert
        with pytest.raises(Exception, match="Search service unavailable"):
            handler.handle(search_memory_query)

    def test_handler_maintains_result_ordering(
        self,
        handler: SearchMemoryQueryHandler,
        search_memory_query: SearchMemoryQuery,
        mock_memory_repository: Mock
    ) -> None:
        """Test that handler maintains the ordering from repository results."""
        # Arrange
        ordered_results = [
            MemoryQueryResult(
                memory_id="mem1",
                user_id="user123",
                content="High relevance",
                relevance_score=0.95
            ),
            MemoryQueryResult(
                memory_id="mem2",
                user_id="user123",
                content="Medium relevance",
                relevance_score=0.75
            ),
            MemoryQueryResult(
                memory_id="mem3",
                user_id="user123",
                content="Low relevance",
                relevance_score=0.55
            )
        ]
        mock_memory_repository.search.return_value = ordered_results

        # Act
        result = handler.handle(search_memory_query)

        # Assert
        assert len(result) == 3
        assert result[0].relevance_score == 0.95
        assert result[1].relevance_score == 0.75
        assert result[2].relevance_score == 0.55

    def test_handler_type_safety(
        self,
        handler: SearchMemoryQueryHandler,
        search_memory_query: SearchMemoryQuery,
        mock_memory_repository: Mock
    ) -> None:
        """Test that handler maintains strict typing."""
        # Arrange
        mock_memory_repository.search.return_value = []

        # Act
        result = handler.handle(search_memory_query)

        # Assert - verify return type annotation compliance
        assert isinstance(result, list)
        # All items in list should be MemoryQueryResult if any exist
        for item in result:
            assert isinstance(item, MemoryQueryResult)# from app.service_layer.query_handlers.memory_query_handlers import SearchMemoryQueryHandler
