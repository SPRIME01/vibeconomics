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
    Provides a clean instance of the FastAPI application for each test function.
    Ensures dependency overrides are cleared before and after each test.
    """
    actual_app.dependency_overrides.clear()
    yield actual_app
    actual_app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def client(app_instance: FastAPI) -> Generator[TestClient, None, None]:
    """
    Provides a TestClient instance for making requests to the app.
    Uses the app_instance fixture to ensure a clean app state.
    """
    with TestClient(app_instance) as c:
        yield c

# --- Core Service Mocking Fixtures ---

def _create_mock_fixture(
    app_instance: FastAPI, 
    dependency_provider: Callable[..., Any], 
    service_class: Type[T]
) -> MagicMock:
    """Helper to create and inject a MagicMock for a given service."""
    mock_service = MagicMock(spec=service_class)
    # Common async methods can be pre-mocked here if desired, or configured in tests
    # For instance, if many services have an 'execute' method:
    # if hasattr(service_class, "execute"):
    #     mock_service.execute = AsyncMock()
    app_instance.dependency_overrides[dependency_provider] = lambda: mock_service
    return mock_service

@pytest.fixture
def mock_ai_provider_service(app_instance: FastAPI) -> MagicMock:
    """Provides a MagicMock for AIProviderService, injected via DI."""
    mock_service = _create_mock_fixture(app_instance, get_ai_provider_service, AIProviderService)
    mock_service.get_completion = AsyncMock(return_value="Default mocked AI response.")
    mock_service.generate_text_v2 = AsyncMock(return_value={"text": "Default mocked AI text v2"})
    # Add other common methods if any
    return mock_service

@pytest.fixture
def mock_memory_service(app_instance: FastAPI) -> MagicMock:
    """Provides a MagicMock for AbstractMemoryService, injected via DI."""
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
    """Provides a MagicMock for AbstractUnitOfWork, injected via DI."""
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
    """Provides a MagicMock for AbstractMessageBus, injected via DI."""
    mock = _create_mock_fixture(app_instance, get_message_bus, AbstractMessageBus)
    mock.publish = AsyncMock()
    # mock.handle = AsyncMock() # If your bus also handles messages directly
    return mock

# --- A2AClientAdapter Mocking & External Responses Registry ---

A2A_MOCKED_RESPONSES_REGISTRY: Dict[Tuple[str, str], Any] = {}

@pytest.fixture(scope="function")
def mock_external_a2a_responses() -> Generator[Dict[Tuple[str, str], Any], None, None]:
    """
    Fixture to allow tests to register expected responses or exceptions for A2A calls.
    The registry is cleared for each test.
    Usage in a test:
        mock_external_a2a_responses[("http://some.agent/a2a", "cap_name")] = {"data": "mocked_value"}
        mock_external_a2a_responses[("http://other.agent/a2a", "cap_fail")] = httpx.ReadTimeout("timeout")
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
    Provides a MagicMock for A2AClientAdapter, injected via DI.
    Its execute_remote_capability method uses responses from mock_external_a2a_responses fixture.
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
    Provides a MagicMock for ActivePiecesAdapter by patching the class.
    This is useful if ActivePiecesAdapter is instantiated directly rather than via DI provider.
    If it has a DI provider, prefer the _create_mock_fixture pattern.
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
    Applies a common set of core service mocks using FastAPI's dependency_overrides.
    This is a convenience fixture. Individual mock fixtures are still available.
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
