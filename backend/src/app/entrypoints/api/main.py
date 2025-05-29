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
    """
    Returns a welcome message for the root endpoint of the application.
    
    Returns:
        A dictionary containing a welcome message.
    """
    return {"message": "Welcome to Vibeconomics Agentic Framework"}


@api_router.post("/test-di-uow", tags=["default"])
async def test_di_uow(uow: UoWDep) -> dict[str, bool]:
    """
    Tests the injection of a Unit of Work dependency.
    
    Checks if the provided unit of work is an instance of AbstractUnitOfWork and reports whether it has been committed.
    
    Returns:
        A dictionary with keys:
            - "is_uow_instance": True if the injected object is an AbstractUnitOfWork.
            - "committed": True if the unit of work has a 'committed' attribute set to True; otherwise, False.
    """
    is_uow_instance = isinstance(uow, AbstractUnitOfWork)
    return {
        "is_uow_instance": is_uow_instance,
        "committed": getattr(uow, "committed", False),
    }


@api_router.post("/test-di-message-bus", tags=["default"])
async def test_di_message_bus(bus: MessageBusDep) -> dict[str, bool]:
    """
    Tests whether the injected message bus is an instance of AbstractMessageBus.
    
    Returns:
        A dictionary with a boolean indicating if the injected bus is an AbstractMessageBus.
    """
    is_bus_instance = isinstance(bus, AbstractMessageBus)
    return {"is_bus_instance": is_bus_instance}


# Example of using the concrete dependency getters directly if needed
@api_router.post("/test-di-concrete-uow", tags=["default"])
async def test_di_concrete_uow(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> dict[str, bool]:
    """
    Tests direct injection of a unit of work using the concrete dependency getter.
    
    Returns:
        A dictionary indicating whether the injected unit of work is an instance of AbstractUnitOfWork.
    """
    return {"is_uow_instance": isinstance(uow, AbstractUnitOfWork)}


# If you need to override dependencies for testing, FastAPI supports this.
# e.g., app.dependency_overrides[get_uow] = lambda: mock_uow # This would be done on the main 'app' instance in fastapi_app.py
