from typing import Any

from pydantic import BaseModel


class StoreMemoryCommand(BaseModel):
    user_id: str
    text_content: str
    metadata: dict[str, Any] | None = None
