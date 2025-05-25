from typing import Optional
from pydantic import BaseModel

class SearchMemoryQuery(BaseModel):
    user_id: str
    search_text: str
    limit: Optional[int] = 10
