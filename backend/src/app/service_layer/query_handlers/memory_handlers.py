from app.adapters.mem0_adapter import AbstractMemoryRepository
from app.domain.memory.models import (
    MemoryQuery,
    MemoryQueryResult,
    MemorySearchResultItem,
)
from app.service_layer.queries.memory import SearchMemoryQuery  # Uncommented


class SearchMemoryQueryHandler:
    """Handles the SearchMemoryQuery."""

    def __init__(self, memory_repo: AbstractMemoryRepository):
        """
        Initializes the handler.

        Args:
            memory_repo: The repository for accessing memory storage.
        """
        self.memory_repo = memory_repo

    async def handle(
        self, query: SearchMemoryQuery
    ) -> MemoryQueryResult:  # Restored type hint and return type
        """
        Processes the SearchMemoryQuery.
        1. Constructs a domain MemoryQuery from the application SearchMemoryQuery DTO.
        2. Uses the memory repository to search for memories.
        3. Returns the results, perhaps wrapped in a MemoryQueryResult DTO.
        """
        # Construct the domain query object to pass to the repository
        domain_query = MemoryQuery(
            user_id=query.user_id,
            search_text=query.search_text,
            limit=query.limit,
            # min_score could be added if present in SearchMemoryQuery app DTO
        )

        search_results: list[MemorySearchResultItem] = self.memory_repo.search(
            domain_query
        )

        # Wrap results in the MemoryQueryResult DTO
        return MemoryQueryResult(
            query=domain_query,  # Echo back the domain query used
            results=search_results,
        )
