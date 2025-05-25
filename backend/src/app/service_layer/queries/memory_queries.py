from pydantic import BaseModel

# from app.domain.memory.models import MemoryQueryResult


class SearchMemoryQuery(BaseModel):
    user_id: str
    search_text: str
    limit: int = 10
