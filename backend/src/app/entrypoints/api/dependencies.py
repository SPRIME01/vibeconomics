from collections.abc import Callable
from typing import Annotated, Any

import httpx
from fastapi import Depends

from app.adapters.a2a_client_adapter import A2AClientAdapter
from app.adapters.message_bus_inmemory import InMemoryMessageBus
from app.adapters.uow_sqlmodel import SqlModelUnitOfWork
from app.service_layer.a2a_service import A2ACapabilityService, A2AHandlerService
from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService
from app.service_layer.ai_provider_service import AIProviderService
from app.service_layer.context_service import ContextService
from app.service_layer.memory_service import AbstractMemoryService
from app.service_layer.message_bus import AbstractMessageBus
from app.service_layer.pattern_service import PatternService
from app.service_layer.strategy_service import StrategyService
from app.service_layer.template_service import TemplateService
from app.service_layer.unit_of_work import AbstractUnitOfWork


def get_db_session_factory() -> Callable[[], Any]:
    """
    Provides a factory for database sessions.
    """

    class DummySession:
        """A dummy session class for DI testing without a real database."""

        def commit(self) -> None:
            """Simulates committing a transaction."""
            pass

        def rollback(self) -> None:
            """Simulates rolling back a transaction."""
            pass

        def close(self) -> None:
            """Simulates closing a session."""
            pass

        def __enter__(self) -> "DummySession":
            """Allows use as a context manager."""
            return self

        def __exit__(self, *args: Any) -> None:
            """Handles exiting the context."""
            pass

    def dummy_session_factory() -> DummySession:
        """Creates and returns a new DummySession instance."""
        return DummySession()

    return dummy_session_factory


# Global instance of message bus
message_bus_instance: AbstractMessageBus = InMemoryMessageBus()


def get_uow(
    session_factory: Annotated[Callable[[], Any], Depends(get_db_session_factory)],
) -> AbstractUnitOfWork:
    """FastAPI dependency injector for Unit of Work."""
    return SqlModelUnitOfWork(session_factory=session_factory)


def get_message_bus() -> AbstractMessageBus:
    """FastAPI dependency injector for Message Bus."""
    return message_bus_instance


# Singleton HTTP client for A2A communications
_http_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client for A2A communications."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


def get_a2a_client_adapter(
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> A2AClientAdapter:
    """Dependency for A2A client adapter."""
    return A2AClientAdapter(http_client=http_client)


def get_template_service(
    a2a_client_adapter: A2AClientAdapter = Depends(get_a2a_client_adapter),
) -> TemplateService:
    """Dependency for template service with A2A client adapter."""
    return TemplateService(a2a_client_adapter=a2a_client_adapter)


from pathlib import Path

# Determine the base path relative to this file, to locate the 'patterns' directory
# This file is in src/app/entrypoints/api/dependencies.py
# Patterns directory is in src/app/patterns/
# So, we need to go up two levels from 'api' to 'app', then into 'patterns'.
PATTERNS_DIRECTORY = Path(__file__).parent.parent.parent / "patterns"

def get_pattern_service() -> PatternService:
    """Dependency for pattern service."""
    return PatternService(patterns_dir_path=PATTERNS_DIRECTORY.resolve())


def get_strategy_service() -> StrategyService:
    """Dependency for strategy service."""
    return StrategyService()


def get_context_service() -> ContextService:
    """Dependency for context service."""
    return ContextService()


def get_ai_provider_service() -> AIProviderService:
    """Dependency for AI provider service."""
    return AIProviderService()


def get_unit_of_work() -> AbstractUnitOfWork:
    """Dependency for unit of work."""
    from app.adapters.fake_unit_of_work import FakeUnitOfWork

    return FakeUnitOfWork()


def get_memory_service() -> AbstractMemoryService | None:
    """Dependency for memory service."""
    return None


def get_ai_pattern_execution_service(
    pattern_service: PatternService = Depends(get_pattern_service),
    template_service: TemplateService = Depends(get_template_service),
    strategy_service: StrategyService = Depends(get_strategy_service),
    context_service: ContextService = Depends(get_context_service),
    ai_provider_service: AIProviderService = Depends(get_ai_provider_service),
    uow: AbstractUnitOfWork = Depends(get_unit_of_work),
    memory_service: AbstractMemoryService | None = Depends(get_memory_service),
    a2a_client_adapter: A2AClientAdapter = Depends(get_a2a_client_adapter),
) -> AIPatternExecutionService:
    """Dependency for AI pattern execution service with all required dependencies."""
    return AIPatternExecutionService(
        pattern_service=pattern_service,
        template_service=template_service,
        strategy_service=strategy_service,
        context_service=context_service,
        ai_provider_service=ai_provider_service,
        uow=uow,
        memory_service=memory_service,
        a2a_client_adapter=a2a_client_adapter,
    )


def get_a2a_capability_service() -> A2ACapabilityService:
    """Dependency for A2A capability service."""
    return A2ACapabilityService()


def get_a2a_handler_service() -> A2AHandlerService:
    """Dependency for A2A handler service."""
    return A2AHandlerService()


async def cleanup_dependencies():
    """Cleanup function to close HTTP client and other resources."""
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None


# Type Aliases for FastAPI dependencies
UoWDep = Annotated[AbstractUnitOfWork, Depends(get_uow)]
MessageBusDep = Annotated[AbstractMessageBus, Depends(get_message_bus)]
