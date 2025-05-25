from .unit_of_work import AbstractUnitOfWork
from .message_bus import AbstractMessageBus

# Try to import LLM services, but don't fail if dependencies are missing
# This makes tests more resilient when optional dependencies aren't installed
try:
    from .llm_services import AbstractLLMService, DSPyLLMService
    __all__ = [
        "AbstractUnitOfWork",
        "AbstractMessageBus",
        "AbstractLLMService",
        "DSPyLLMService"
    ]
except ImportError:
    # Define fallback for testing when dspy is not available
    class AbstractLLMService:
        """Placeholder when dspy package is not available."""
        pass

    class DSPyLLMService(AbstractLLMService):
        """Placeholder when dspy package is not available."""
        pass

    __all__ = [
        "AbstractUnitOfWork",
        "AbstractMessageBus",
        "AbstractLLMService",
        "DSPyLLMService"
    ]
