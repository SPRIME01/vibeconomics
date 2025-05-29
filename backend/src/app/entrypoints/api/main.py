from fastapi import APIRouter, Depends

from app.core.base_aggregate import DomainEvent  # For type hint
from app.service_layer.message_bus import AbstractMessageBus
from app.service_layer.unit_of_work import AbstractUnitOfWork

# Import the new router
from app.entrypoints.api.routes import (
    copilot_api,
    # Import other route modules if they exist and need to be included
    # e.g., items, users, login, etc.
    # For now, only copilot_api is explicitly mentioned as included.
    # The original file had @app.get("/") etc., which will now be part of this router.
)
from .dependencies import MessageBusDep, UoWDep, get_uow

api_router = APIRouter()

# Include the Copilot API router
api_router.include_router(copilot_api.router, prefix="/copilot", tags=["copilot"])


# Example Event for testing
class TestDIEvent(DomainEvent):
    """A sample domain event for testing DI."""

    message: str


@api_router.get("/", tags=["default"])
async def read_root() -> dict[str, str]:
    """Root endpoint for the application."""
    return {"message": "Welcome to Vibeconomics Agentic Framework"}


@api_router.post("/test-di-uow", tags=["default"])
async def test_di_uow(uow: UoWDep) -> dict[str, bool]:
    """
    Endpoint to test Unit of Work dependency injection.

    Verifies that the injected 'uow' is an instance of AbstractUnitOfWork.
    """
    is_uow_instance = isinstance(uow, AbstractUnitOfWork)
    return {
        "is_uow_instance": is_uow_instance,
        "committed": getattr(uow, "committed", False),
    }


@api_router.post("/test-di-message-bus", tags=["default"])
async def test_di_message_bus(bus: MessageBusDep) -> dict[str, bool]:
    """
    Endpoint to test MessageBus dependency injection.

    Verifies that the injected 'bus' is an instance of AbstractMessageBus.
    """
    is_bus_instance = isinstance(bus, AbstractMessageBus)
    return {"is_bus_instance": is_bus_instance}


# Example of using the concrete dependency getters directly if needed
@api_router.post("/test-di-concrete-uow", tags=["default"])
async def test_di_concrete_uow(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> dict[str, bool]:
    """
    Endpoint to test direct injection of UoW using the getter.

    Verifies that the injected 'uow' is an instance of AbstractUnitOfWork.
    """
    return {"is_uow_instance": isinstance(uow, AbstractUnitOfWork)}


# If you need to override dependencies for testing, FastAPI supports this.
# e.g., app.dependency_overrides[get_uow] = lambda: mock_uow # This would be done on the main 'app' instance in fastapi_app.py
