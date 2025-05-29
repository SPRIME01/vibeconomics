import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, Callable, Generator, Coroutine, List, Tuple, TypeVar, Type
from pydantic import BaseModel
import httpx # For A2AClientAdapter if it needs an http_client
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Application instance
from src.app.entrypoints.fastapi_app import app as actual_app # Renamed to avoid conflict

# Service and Adapter Classes
from src.app.service_layer.ai_provider_service import AIProviderService
from src.app.service_layer.memory_service import AbstractMemoryService
from src.app.adapters.a2a_client_adapter import A2AClientAdapter
from src.app.adapters.activepieces_adapter import ActivePiecesAdapter
from src.app.service_layer.unit_of_work import AbstractUnitOfWork
from src.app.service_layer.message_bus import AbstractMessageBus

# Dependency provider functions (getter functions)
from src.app.entrypoints.api.dependencies import (
    get_ai_provider_service,
    get_memory_service,
    get_a2a_client_adapter,
    get_unit_of_work,
    get_message_bus,
    # No specific provider for ActivePiecesAdapter, will be patched directly if needed
)

T = TypeVar('T')

# --- General Purpose Fixtures ---

@pytest.fixture(scope="function")
def app_instance() -> Generator[FastAPI, None, None]:
    """
    Yields a clean FastAPI application instance for each test function.
    
    Clears all dependency overrides before and after each test to ensure isolation between tests.
    """
    actual_app.dependency_overrides.clear()
    yield actual_app
    actual_app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def client(app_instance: FastAPI) -> Generator[TestClient, None, None]:
    """
    Yields a TestClient for making HTTP requests to the FastAPI app.
    
    Ensures each test receives a fresh TestClient instance tied to a clean app state.
    """
    with TestClient(app_instance) as c:
        yield c

# --- Core Service Mocking Fixtures ---

def _create_mock_fixture(
    app_instance: FastAPI, 
    dependency_provider: Callable[..., Any], 
    service_class: Type[T]
) -> MagicMock:
    """
    Creates and injects a MagicMock for the specified service class into the FastAPI app's dependency overrides.
    
    Args:
        app_instance: The FastAPI application instance to modify.
        dependency_provider: The dependency provider function to override.
        service_class: The class to use as a specification for the MagicMock.
    
    Returns:
        A MagicMock instance configured for the given service class.
    """
    mock_service = MagicMock(spec=service_class)
    # Common async methods can be pre-mocked here if desired, or configured in tests
    # For instance, if many services have an 'execute' method:
    # if hasattr(service_class, "execute"):
    #     mock_service.execute = AsyncMock()
    app_instance.dependency_overrides[dependency_provider] = lambda: mock_service
    return mock_service

@pytest.fixture
def mock_ai_provider_service(app_instance: FastAPI) -> MagicMock:
    """
    Provides a MagicMock instance of AIProviderService for testing.
    
    The mock is injected into the FastAPI app's dependency overrides and includes async mocks for `get_completion` and `generate_text_v2` methods with default return values.
    """
    mock_service = _create_mock_fixture(app_instance, get_ai_provider_service, AIProviderService)
    mock_service.get_completion = AsyncMock(return_value="Default mocked AI response.")
    mock_service.generate_text_v2 = AsyncMock(return_value={"text": "Default mocked AI text v2"})
    # Add other common methods if any
    return mock_service

@pytest.fixture
def mock_memory_service(app_instance: FastAPI) -> MagicMock:
    """
    Provides a MagicMock instance for AbstractMemoryService and injects it into the FastAPI app's dependency overrides.
    
    The mock includes async methods for memory operations, returning default values suitable for isolated testing.
    """
    mock_service = _create_mock_fixture(app_instance, get_memory_service, AbstractMemoryService)
    # Configure common AbstractMemoryService methods
    mock_service.get_memory = AsyncMock(return_value=None)
    mock_service.add_memory = AsyncMock()
    mock_service.update_memory = AsyncMock()
    mock_service.delete_memory = AsyncMock()
    mock_service.search_memory = AsyncMock(return_value=[])
    mock_service.get_conversation_history = AsyncMock(return_value=[])
    return mock_service

@pytest.fixture
def mock_uow(app_instance: FastAPI) -> MagicMock:
    """
    Provides a MagicMock instance of AbstractUnitOfWork for dependency injection in tests.
    
    The mock includes async commit and rollback methods, a mock conversations repository,
    and supports usage as an async context manager.
    """
    mock = _create_mock_fixture(app_instance, get_unit_of_work, AbstractUnitOfWork)
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    # Example of mocking a repository if UoW provides them as attributes
    mock.conversations = MagicMock() 
    # mock.items = MagicMock() # Add other repositories as needed
    
    # Make the UoW usable as an async context manager
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=None)
    return mock

@pytest.fixture
def mock_message_bus(app_instance: FastAPI) -> MagicMock:
    """
    Provides a MagicMock instance for AbstractMessageBus and injects it into the FastAPI app's dependency overrides.
    
    The mock's async `publish` method is set up for use in tests.
    """
    mock = _create_mock_fixture(app_instance, get_message_bus, AbstractMessageBus)
    mock.publish = AsyncMock()
    # mock.handle = AsyncMock() # If your bus also handles messages directly
    return mock

# --- A2AClientAdapter Mocking & External Responses Registry ---

A2A_MOCKED_RESPONSES_REGISTRY: Dict[Tuple[str, str], Any] = {}

@pytest.fixture(scope="function")
def mock_external_a2a_responses() -> Generator[Dict[Tuple[str, str], Any], None, None]:
    """
    Provides a per-test registry for mocking responses or exceptions to A2A client adapter calls.
    
    Clears the registry before and after each test to ensure isolation. Tests can populate the registry with expected responses or exceptions keyed by (agent_url, capability_name) tuples.
    """
    A2A_MOCKED_RESPONSES_REGISTRY.clear()
    yield A2A_MOCKED_RESPONSES_REGISTRY
    A2A_MOCKED_RESPONSES_REGISTRY.clear()

@pytest.fixture
def mock_a2a_client_adapter(
    app_instance: FastAPI, 
    mock_external_a2a_responses: Dict[Tuple[str, str], Any]
) -> MagicMock:
    """
    Provides a MagicMock for A2AClientAdapter, injecting it into FastAPI's dependency overrides.
    
    The mock's execute_remote_capability method returns predefined responses or raises exceptions based on the mock_external_a2a_responses registry, keyed by (agent_url, capability_name). If a response_model is specified and the mocked response is a dict, it attempts to parse the response into the model, failing the test if parsing fails. If an unmocked call occurs, the test fails with an error message.
    
    Returns:
        The MagicMock instance for A2AClientAdapter.
    """
    # Create a mock instance of A2AClientAdapter.
    # The http_client it normally takes won't be used by the mocked method.
    mock_adapter_instance = MagicMock(spec=A2AClientAdapter)

    async def _execute_remote_capability_side_effect(
        agent_url: str,
        capability_name: str,
        request_payload: BaseModel, 
        response_model: Type[BaseModel] | None = None, # Corrected type hint
    ) -> Any: # Returns Pydantic model instance or dict
        """
        Simulates the execution of a remote capability call for testing, returning a mocked response or raising a mocked exception.
        
        If a mock response or exception is registered for the given (agent_url, capability_name) key, returns the response or raises the exception. If a response_model is provided and the mock is a dict, attempts to parse it into the model, failing the test if parsing fails. Fails the test if the call is not mocked.
        """
        key = (agent_url, capability_name)
        if key in mock_external_a2a_responses:
            response_or_exception = mock_external_a2a_responses[key]
            if isinstance(response_or_exception, Exception):
                raise response_or_exception
            
            if response_model and isinstance(response_or_exception, dict):
                try:
                    return response_model(**response_or_exception)
                except Exception as e: # Catch Pydantic validation error or other issues
                    pytest.fail(f"Failed to parse mocked response for {key} into {response_model.__name__}: {e}")
            return response_or_exception 
        
        # Fallback for unmocked calls
        # In strict tests, any unmocked call should ideally fail.
        # Consider raising an error or using pytest.fail here.
        error_msg = f"A2A call to {agent_url}/{capability_name} was not mocked by mock_external_a2a_responses."
        # To make debugging easier, print the expected key:
        # print(f"Missing mock for key: ('{agent_url}', '{capability_name}')")
        # print(f"Available mocks: {list(mock_external_a2a_responses.keys())}")
        pytest.fail(error_msg) # Make tests fail if an A2A call was not expected & mocked
        # Unreachable, but satisfies type checker if pytest.fail was commented out
        # return {} # Or some default error structure

    mock_adapter_instance.execute_remote_capability = AsyncMock(side_effect=_execute_remote_capability_side_effect)
    
    # Apply the override using the app_instance fixture
    app_instance.dependency_overrides[get_a2a_client_adapter] = lambda: mock_adapter_instance
    
    return mock_adapter_instance

@pytest.fixture
def mock_active_pieces_adapter() -> Generator[MagicMock, None, None]:
    """
    Yields a MagicMock instance of ActivePiecesAdapter with async methods mocked for testing.
    
    This fixture patches the ActivePiecesAdapter class so that any instantiation within the test context returns a MagicMock. The run_flow method is mocked to return a fixed success response. Use this fixture when ActivePiecesAdapter is instantiated directly rather than injected via dependency overrides.
    """
    # Assuming ActivePiecesAdapter is imported as:
    # from src.app.adapters.activepieces_adapter import ActivePiecesAdapter
    # The patch path should be where it's looked up (imported or defined).
    # If it's imported into a service, that service's module path is used for patching.
    # For now, let's assume we patch its definition directly for broader coverage.
    # This is a placeholder; actual usage would determine the best patch target.
    with patch("src.app.adapters.activepieces_adapter.ActivePiecesAdapter", spec=True) as mock_class:
        # mock_class.return_value is the mock instance if ActivePiecesAdapter() is called
        instance_mock = mock_class.return_value 
        instance_mock.run_flow = AsyncMock(return_value={"status": "success", "output": "mocked_activepieces_flow_output"})
        # Add other methods as needed
        # instance_mock.get_piece_metadata = AsyncMock(return_value=...)
        yield instance_mock # This yields the mock *instance*

# --- Convenience Fixture to Apply Multiple Mocks ---
@pytest.fixture
def apply_core_service_mocks(
    app_instance: FastAPI, # To apply overrides
    mock_ai_provider_service: MagicMock,
    mock_memory_service: MagicMock,
    mock_uow: MagicMock,
    mock_message_bus: MagicMock,
    # Note: mock_a2a_client_adapter is not included here due to its dependency on mock_external_a2a_responses
    # Tests needing A2A mocking should request mock_a2a_client_adapter (and mock_external_a2a_responses) explicitly.
) -> None:
    """
    Convenience fixture to request multiple core service mocks in tests.
    
    This fixture ensures that the core service mocks for AI provider, memory, unit of work, and message bus are available and their dependency overrides are applied to the FastAPI app instance. It does not perform additional actions, as each individual mock fixture manages its own override.
    """
    # Overrides are already applied within each individual mock fixture that uses app_instance.
    # This fixture primarily serves as a way to request multiple mocks easily.
    # No direct action needed here if individual fixtures already set overrides.
    # If they didn't, this is where you'd do:
    # app_instance.dependency_overrides[get_ai_provider_service] = lambda: mock_ai_provider_service
    # ... etc.
    # However, the current pattern is that each mock fixture using app_instance handles its own override.
    pass

# --- Test Structure Review Placeholder ---
# This section would be filled after manual review of the directory structure.

# --- Typing Check Placeholder for E2E Tests ---
# This section would be filled after manual review and updates to E2E test files.
