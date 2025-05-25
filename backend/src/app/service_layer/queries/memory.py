from pydantic import BaseModel


class SearchMemoryQuery(BaseModel):
    user_id: str
    search_text: str
    limit: int | None = 10
