from typing import Optional, Dict, Any
from pydantic import BaseModel

class StoreMemoryCommand(BaseModel):
    user_id: str
    text_content: str
    metadata: Optional[Dict[str, Any]] = None
