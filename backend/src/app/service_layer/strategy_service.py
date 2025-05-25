from typing import List, Dict, Any, Optional, Type, Callable, AsyncGenerator, Protocol
from uuid import UUID
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from app.core.base_aggregate import DomainEvent # Adjusted import

class Strategy(BaseModel):
    name: str
    description: str
    prompt: str

class StrategyNotFoundError(Exception):
    pass

class InvalidStrategyFormatError(Exception):
    pass
