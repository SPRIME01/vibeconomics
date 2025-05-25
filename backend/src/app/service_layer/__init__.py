# Try to import LLM services, but don't fail if dependencies are missing
# This makes tests more resilient when optional dependencies aren't installed
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from .message_bus import AbstractMessageBus
from .unit_of_work import AbstractUnitOfWork

PydanticModelT = TypeVar("PydanticModelT", bound=BaseModel)

_llm_services_available = False
try:
    from .llm_services import AbstractLLMService as _RealAbstractLLMService
    from .llm_services import DSPyLLMService as _RealDSPyLLMService

    AbstractLLMService = _RealAbstractLLMService  # type: ignore[misc, assignment]
    DSPyLLMService = _RealDSPyLLMService  # type: ignore[misc, assignment]
    _llm_services_available = True
except ImportError:

    class _AbstractLLMServicePlaceholder(Generic[PydanticModelT]):
        """Placeholder when dspy package is not available."""

        def get_response(self, prompt: str, **kwargs: Any) -> str:
            return "dummy response"

        def get_structured_response(
            self, prompt: str, output_model: type[PydanticModelT], **kwargs: Any
        ) -> PydanticModelT:
            # This is a simplified mock, adjust if specific fields are needed for tests
            try:
                return output_model()
            except Exception:
                # Fallback for models that require arguments
                return output_model(
                    **{
                        field_name: None
                        for field_name, f_info in output_model.model_fields.items()
                        if f_info.is_required()
                    }
                )

    class _DSPyLLMServicePlaceholder(_AbstractLLMServicePlaceholder[PydanticModelT]):
        """Placeholder when dspy package is not available."""

        pass

    AbstractLLMService = _AbstractLLMServicePlaceholder  # type: ignore[misc, assignment]
    DSPyLLMService = _DSPyLLMServicePlaceholder  # type: ignore[misc, assignment]

__all__ = [
    "AbstractUnitOfWork",
    "AbstractMessageBus",
    "AbstractLLMService",
    "DSPyLLMService",
]
