from fastapi import Depends, FastAPI

from app.core.base_aggregate import DomainEvent  # For type hint
from app.service_layer.message_bus import AbstractMessageBus  # Removed EventT
from app.service_layer.unit_of_work import AbstractUnitOfWork

# Import the new router
from app.entrypoints.api.routes import copilot_api
from .dependencies import MessageBusDep, UoWDep, get_uow

app = FastAPI(title="Vibeconomics Agentic Framework")

# Include the Copilot API router
app.include_router(copilot_api.router, prefix="/copilot", tags=["copilot"])


# Example Event for testing
class TestDIEvent(DomainEvent):
    """A sample domain event for testing DI."""

    message: str


@app.get("/")
async def read_root() -> dict[str, str]:
    """Root endpoint for the application."""
    return {"message": "Welcome to Vibeconomics Agentic Framework"}


@app.post("/test-di-uow")
async def test_di_uow(uow: UoWDep) -> dict[str, bool]:
    """
    Endpoint to test Unit of Work dependency injection.

    Verifies that the injected 'uow' is an instance of AbstractUnitOfWork.
    """
    is_uow_instance = isinstance(uow, AbstractUnitOfWork)
    # In a real scenario, you'd use the uow:
    # with uow:
    #    uow.some_repository.add(...)
    #    uow.commit()
    # The 'committed' attribute check is illustrative; SqlModelUnitOfWork
    # sets 'committed' only if its context manager methods are fully used.
    # Here, we mainly test if the DI provided an object of the correct abstract type.
    return {
        "is_uow_instance": is_uow_instance,
        "committed": getattr(uow, "committed", False),
    }


@app.post("/test-di-message-bus")
async def test_di_message_bus(bus: MessageBusDep) -> dict[str, bool]:
    """
    Endpoint to test MessageBus dependency injection.

    Verifies that the injected 'bus' is an instance of AbstractMessageBus.
    """
    is_bus_instance = isinstance(bus, AbstractMessageBus)
    # In a real scenario, you'd use the bus:
    # event = TestDIEvent(message="Hello from DI test")
    # bus.publish(event)
    return {"is_bus_instance": is_bus_instance}


# Example of using the concrete dependency getters directly if needed
@app.post("/test-di-concrete-uow")
async def test_di_concrete_uow(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> dict[str, bool]:
    """
    Endpoint to test direct injection of UoW using the getter.

    Verifies that the injected 'uow' is an instance of AbstractUnitOfWork.
    """
    return {"is_uow_instance": isinstance(uow, AbstractUnitOfWork)}


# If you need to override dependencies for testing, FastAPI supports this.
# e.g., app.dependency_overrides[get_uow] = lambda: mock_uow
