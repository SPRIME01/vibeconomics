from typing import Optional

from pydantic import BaseModel


class RabbitMQConfig(BaseModel):
    host: str = "localhost"
    port: int = 5672
    username: Optional[str] = None
    password: Optional[str] = None
    virtual_host: str = "/"
