import abc
import uuid

from mem0.client.main import MemoryClient as Mem0  # Updated import based on exploration

from app.domain.memory.models import (
    MemoryId,
    MemoryItem,
    MemoryQuery,
    MemorySearchResultItem,
    MemoryWriteRequest,
)


class AbstractMemoryRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, memory_data: MemoryWriteRequest) -> str | None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, memory_id: str) -> MemoryItem | None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_aggregate_id(self, aggregate_id: MemoryId) -> MemoryItem | None:
        raise NotImplementedError

    @abc.abstractmethod
    def search(self, query: MemoryQuery) -> list[MemorySearchResultItem]:
        raise NotImplementedError


class Mem0Adapter(AbstractMemoryRepository):
    def __init__(self, mem0_client: Mem0) -> None:
        self.client: Mem0 = mem0_client

    def add(self, memory_data: MemoryWriteRequest) -> str | None:
        try:
            # The mem0ai client's add method might return a dict or a string ID
            # based on the previous commented out code.
            # Example: response = self.client.add(...)
            # For now, assuming it returns a structure with an "id" field or the ID directly.
            response_data = self.client.add(
                text=memory_data.text_content,
                user_id=memory_data.user_id,  # Ensure user_id is passed if supported
                metadata=memory_data.metadata,  # Pass metadata if supported
            )
            if isinstance(response_data, dict) and "id" in response_data:
                return str(response_data["id"])
            elif isinstance(response_data, str):
                return response_data
            # print(f"Unexpected response format from Mem0 client on add: {response_data}") # For debugging
            return None
        except Exception as e:
            print(f"Error adding to Mem0 via adapter: {e}")
            return None

    def get(self, memory_id: str) -> MemoryItem | None:
        # Placeholder: Actual implementation depends on mem0ai client's get method
        # try:
        #     data = self.client.get(memory_id)
        #     if data:
        #         return MemoryItem(id=data.get("id"), text_content=data.get("text"), ...) # Adapt fields
        # except Exception as e:
        #     print(f"Error getting from Mem0 via adapter: {e}")
        # return None
        raise NotImplementedError(
            "get method not fully implemented for Mem0Adapter yet."
        )

    def get_by_aggregate_id(self, aggregate_id: MemoryId) -> MemoryItem | None:
        # Placeholder: Actual implementation depends on mem0ai client's get method
        # This might be similar to get() if mem0ai uses string IDs universally.
        raise NotImplementedError(
            "get_by_aggregate_id not implemented for Mem0Adapter."
        )

    def search(self, query: MemoryQuery) -> list[MemorySearchResultItem]:
        try:
            # Assuming mem0ai client's search method takes similar parameters
            results_raw = self.client.search(
                query=query.search_text,
                user_id=query.user_id,  # Ensure user_id is passed if supported
                limit=query.limit,
            )
            processed_results: list[MemorySearchResultItem] = []
            if results_raw and isinstance(
                results_raw, list
            ):  # mem0ai might return a list of results
                for res_item in results_raw:
                    if isinstance(res_item, dict):
                        processed_results.append(
                            MemorySearchResultItem(
                                id=str(
                                    res_item.get("id", uuid.uuid4())
                                ),  # Ensure ID is string
                                text_content=res_item.get("text", ""),
                                metadata=res_item.get("metadata"),
                                score=float(
                                    res_item.get("score", 0.0)
                                ),  # Ensure score is float
                            )
                        )
            return processed_results
        except Exception as e:
            print(f"Error searching Mem0 via adapter: {e}")
            return []
