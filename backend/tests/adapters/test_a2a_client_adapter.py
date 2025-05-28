import json
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio
from pydantic import BaseModel, ValidationError

from app.adapters.a2a_client_adapter import A2AClientAdapter


class MyTestRequest(BaseModel):
    data: str


class MyTestResponse(BaseModel):
    result: str


@pytest_asyncio.fixture
async def mock_httpx_client() -> AsyncMock:
    """
    Asynchronously provides a mocked httpx.AsyncClient for use in tests.

    Returns:
        An AsyncMock instance configured to mimic httpx.AsyncClient.
    """
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def a2a_client_adapter(mock_httpx_client: AsyncMock) -> A2AClientAdapter:
    """
    Creates an instance of A2AClientAdapter using a mocked asynchronous HTTP client.

    This fixture provides an adapter configured for testing with a mock HTTP client to avoid real network calls.
    """
    return A2AClientAdapter(http_client=mock_httpx_client)


@pytest.mark.asyncio
async def test_execute_remote_capability_success_with_response_model(
    a2a_client_adapter: A2AClientAdapter,
    mock_httpx_client: AsyncMock,
) -> None:
    """Test successful execution with response model parsing."""
    # Arrange
    agent_url = "http://test-agent.com"
    capability_name = "test_capability"
    request_payload = MyTestRequest(data="test data")
    response_model = MyTestResponse

    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"result": "test result"})
    mock_response.raise_for_status = AsyncMock(return_value=None)
    mock_httpx_client.post = AsyncMock(return_value=mock_response)

    # Act
    result = await a2a_client_adapter.execute_remote_capability(
        agent_url=agent_url,
        capability_name=capability_name,
        request_payload=request_payload,
        response_model=response_model,
    )

    # Assert
    assert isinstance(result, MyTestResponse)
    assert result.result == "test result"

    mock_httpx_client.post.assert_called_once_with(
        f"{agent_url}/a2a/execute/{capability_name}",
        json={"data": "test data"},
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )


@pytest.mark.asyncio
async def test_execute_remote_capability_success_without_response_model(
    a2a_client_adapter: A2AClientAdapter,
    mock_httpx_client: AsyncMock,
) -> None:
    """Test successful execution returning raw dictionary."""
    # Arrange
    agent_url = "http://test-agent.com"
    capability_name = "test_capability"
    request_payload = MyTestRequest(data="test data")

    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"result": "test result"})
    mock_response.raise_for_status = AsyncMock(return_value=None)
    mock_httpx_client.post = AsyncMock(return_value=mock_response)

    # Act
    result = await a2a_client_adapter.execute_remote_capability(
        agent_url=agent_url,
        capability_name=capability_name,
        request_payload=request_payload,
        response_model=None,
    )

    # Assert
    assert isinstance(result, dict)
    assert result == {"result": "test result"}


@pytest.mark.asyncio
async def test_execute_remote_capability_http_error(
    a2a_client_adapter: A2AClientAdapter,
    mock_httpx_client: AsyncMock,
) -> None:
    """Test handling of HTTP errors."""
    # Arrange
    agent_url = "http://test-agent.com"
    capability_name = "test_capability"
    request_payload = MyTestRequest(data="test data")

    mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=None, response=None
    )

    # Act & Assert
    with pytest.raises(httpx.HTTPStatusError):
        await a2a_client_adapter.execute_remote_capability(
            agent_url=agent_url,
            capability_name=capability_name,
            request_payload=request_payload,
        )


@pytest.mark.asyncio
async def test_execute_remote_capability_network_error(
    a2a_client_adapter: A2AClientAdapter,
    mock_httpx_client: AsyncMock,
) -> None:
    """Test handling of network errors."""
    # Arrange
    agent_url = "http://test-agent.com"
    capability_name = "test_capability"
    request_payload = MyTestRequest(data="test data")

    mock_httpx_client.post.side_effect = httpx.NetworkError("Connection failed")

    # Act & Assert
    with pytest.raises(httpx.NetworkError):
        await a2a_client_adapter.execute_remote_capability(
            agent_url=agent_url,
            capability_name=capability_name,
            request_payload=request_payload,
        )


@pytest.mark.asyncio
async def test_execute_remote_capability_json_decode_error(
    a2a_client_adapter: A2AClientAdapter,
    mock_httpx_client: AsyncMock,
) -> None:
    """Test handling of JSON decode errors."""
    # Arrange
    agent_url = "http://test-agent.com"
    capability_name = "test_capability"
    request_payload = MyTestRequest(data="test data")

    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock(return_value=None)
    mock_response.json = AsyncMock(
        side_effect=json.JSONDecodeError("Invalid JSON", "", 0)
    )
    mock_httpx_client.post = AsyncMock(return_value=mock_response)

    # Act & Assert
    with pytest.raises(RuntimeError, match="Failed to decode JSON response"):
        await a2a_client_adapter.execute_remote_capability(
            agent_url=agent_url,
            capability_name=capability_name,
            request_payload=request_payload,
        )


@pytest.mark.asyncio
async def test_execute_remote_capability_validation_error(
    a2a_client_adapter: A2AClientAdapter,
    mock_httpx_client: AsyncMock,
) -> None:
    """Test handling of validation errors when parsing response."""
    # Arrange
    agent_url = "http://test-agent.com"
    capability_name = "test_capability"
    request_payload = MyTestRequest(data="test data")
    response_model = MyTestResponse

    mock_response = AsyncMock()
    mock_response.json = AsyncMock(
        return_value={"invalid": "data"}
    )  # Missing 'result' field
    mock_response.raise_for_status = AsyncMock(return_value=None)
    mock_httpx_client.post = AsyncMock(return_value=mock_response)

    # Act & Assert
    with pytest.raises(ValidationError):
        await a2a_client_adapter.execute_remote_capability(
            agent_url=agent_url,
            capability_name=capability_name,
            request_payload=request_payload,
            response_model=response_model,
        )
