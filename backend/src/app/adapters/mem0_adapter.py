import abc
import uuid
from typing import List, Optional, Any, Dict

try:
    from mem0.client import Mem0 # Try this first
except ImportError:
    from mem0 import Mem0 # Fallback

from app.domain.memory.models import (
    MemoryItem, MemoryWriteRequest, MemoryQuery,
    MemorySearchResultItem, MemoryId
)

class AbstractMemoryRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, memory_data: MemoryWriteRequest) -> Optional[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, memory_id: str) -> Optional[MemoryItem]:
        raise NotImplementedError
    
    @abc.abstractmethod
    def get_by_aggregate_id(self, aggregate_id: MemoryId) -> Optional[MemoryItem]:
        raise NotImplementedError

    @abc.abstractmethod
    def search(self, query: MemoryQuery) -> List[MemorySearchResultItem]:
        raise NotImplementedError

class Mem0Adapter(AbstractMemoryRepository):
    def __init__(self, mem0_client: Mem0) -> None:
        self.client: Mem0 = mem0_client

    def add(self, memory_data: MemoryWriteRequest) -> Optional[str]:
        try:
            response = self.client.add(
                text=memory_data.text_content,
                user_id=memory_data.user_id,
                metadata=memory_data.metadata
            )
            if isinstance(response, dict) and "id" in response:
                return response["id"]
            elif isinstance(response, str):
                return response
            # Adding a print for unexpected response structure, helps in debugging
            # print(f"Unexpected response format from Mem0 client on add: {response}") # Commented out as per prompt
            return None
        except Exception as e:
            print(f"Error adding to Mem0 via adapter: {e}") 
            return None
    
    def get(self, memory_id: str) -> Optional[MemoryItem]:
        raise NotImplementedError("get method not fully implemented for Mem0Adapter yet.")

    def get_by_aggregate_id(self, aggregate_id: MemoryId) -> Optional[MemoryItem]:
        raise NotImplementedError("get_by_aggregate_id not implemented for Mem0Adapter.")

    def search(self, query: MemoryQuery) -> List[MemorySearchResultItem]:
        try:
            results_raw = self.client.search(
                query=query.search_text,
                user_id=query.user_id,
                limit=query.limit
            )
            processed_results: List[MemorySearchResultItem] = []
            if results_raw: # Ensure results_raw is not None and is iterable
                for res_item in results_raw:
                    if isinstance(res_item, dict):
                         processed_results.append(
                            MemorySearchResultItem(
                                id=res_item.get("id", ""), 
                                text_content=res_item.get("text", ""),
                                metadata=res_item.get("metadata"),
                                score=res_item.get("score")
                            )
                        )
                    # Add handling for other possible types of res_item if necessary
            return processed_results
        except Exception as e:
            print(f"Error searching Mem0 via adapter: {e}")
            return []
