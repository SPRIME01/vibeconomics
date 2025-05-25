from pydantic import BaseModel


class Strategy(BaseModel):
    name: str
    description: str
    prompt: str


class StrategyNotFoundError(Exception):
    pass


class InvalidStrategyFormatError(Exception):
    pass
