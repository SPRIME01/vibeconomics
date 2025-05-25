from typing import List, Dict, Any, Optional, Type, Callable, AsyncGenerator, Protocol
from uuid import UUID
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from app.core.base_aggregate import DomainEvent # Adjusted import
# from .pattern_service import PatternService
# from .template_service import TemplateService
# ... other engine service imports
# from app.domain.agent.ports import AbstractConversationRepository
