import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any, Optional, Type, Callable, AsyncGenerator
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
# from app.service_layer.unit_of_work import AbstractUnitOfWork
# from app.service_layer.message_bus import AbstractMessageBus
