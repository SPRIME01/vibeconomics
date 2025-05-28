import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from pydantic import BaseModel, ValidationError
from typing import Type

import httpx 
# from httpx import AsyncClient, Request, Response, NetworkError, HTTPStatusError # This is also fine

from app.adapters.a2a_client_adapter import A2AClientAdapter # Import the actual adapter


# Sample Pydantic models for request and response
# from app.domain.a2a.models import SummarizeTextA2ARequest, SummarizeTextA2AResponse
# Using local MyTestRequest/Response for simplicity in this test file
class MyTestRequest(BaseModel):
    data: str

class MyTestResponse(BaseModel):
    result: str


@pytest_asyncio.fixture
async def mock_httpx_client() -> AsyncMock:
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def a2a_client_adapter(mock_httpx_client: AsyncMock) -> A2AClientAdapter: # Type hint uses the imported adapter
    return A2AClientAdapter(http_client=mock_httpx_client)


@pytest.mark.asyncio
async def test_execute_remote_capability_success(
    a2a_client_adapter: A2AClientAdapter, 
    mock_httpx_client: AsyncMock
):
    agent_url = "http://fakeagent.com"
    capability_name = "test_capability"
    request_payload = MyTestRequest(data="input_data")
    
    # Prepare a mocked httpx.Response
    mock_response_json = {"result": "output_data"}
    # Note: httpx.Response needs a request object for certain attributes if accessed by the code under test
    # For this test, if only .json() and .status_code are used by raise_for_status, it's fine.
    mock_http_response = httpx.Response(
        status_code=200, 
        json=mock_response_json, 
        request=httpx.Request("POST", f"{agent_url}/a2a/execute/{capability_name}")
    )
    mock_httpx_client.post.return_value = mock_http_response
    
    result = await a2a_client_adapter.execute_remote_capability(
        agent_url, capability_name, request_payload, response_model=MyTestResponse
    )
    
    expected_url = f"{agent_url}/a2a/execute/{capability_name}"
    # Call mock_httpx_client.post.assert_called_once_with with url as a positional argument
    mock_httpx_client.post.assert_called_once_with(
        expected_url, # url as positional
        json=request_payload.model_dump(),
        headers={"Content-Type": "application/json", "Accept": "application/json"}
    )
    
    assert isinstance(result, MyTestResponse)
    assert result.result == "output_data"


@pytest.mark.asyncio
async def test_execute_remote_capability_http_error(
    a2a_client_adapter: A2AClientAdapter, 
    mock_httpx_client: AsyncMock
):
    agent_url = "http://fakeagent.com"
    capability_name = "test_capability_http_error"
    request_payload = MyTestRequest(data="input_data_http_error")
    
    mock_request = httpx.Request(method="POST", url=f"{agent_url}/a2a/execute/{capability_name}")
    error_response = httpx.Response(500, json={"detail": "Server error"}, request=mock_request)
    
    mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
        "Server error", request=mock_request, response=error_response
    )
    
    with pytest.raises(httpx.HTTPStatusError) as excinfo:
        await a2a_client_adapter.execute_remote_capability(
            agent_url, capability_name, request_payload, response_model=MyTestResponse
        )
    
    assert excinfo.value.response.status_code == 500
    assert excinfo.value.request == mock_request


@pytest.mark.asyncio
async def test_execute_remote_capability_network_error(
    a2a_client_adapter: A2AClientAdapter, 
    mock_httpx_client: AsyncMock
):
    agent_url = "http://fakeagent.com"
    capability_name = "test_capability_network_error"
    request_payload = MyTestRequest(data="input_data_network_error")
    
    # The request object passed to NetworkError is what httpx would have created
    mock_request_for_error = httpx.Request(method="POST", url=f"{agent_url}/a2a/execute/{capability_name}")

    mock_httpx_client.post.side_effect = httpx.NetworkError(
        "Connection failed", request=mock_request_for_error
    )
    
    with pytest.raises(httpx.NetworkError):
        await a2a_client_adapter.execute_remote_capability(
            agent_url, capability_name, request_payload, response_model=MyTestResponse
        )


@pytest.mark.asyncio
async def test_execute_remote_capability_invalid_response_payload(
    a2a_client_adapter: A2AClientAdapter, 
    mock_httpx_client: AsyncMock
):
    agent_url = "http://fakeagent.com"
    capability_name = "test_capability_invalid_payload"
    request_payload = MyTestRequest(data="input_data_invalid_payload")
    
    # Mock response with a payload that doesn't match MyTestResponse
    mock_response_json = {"wrong_field": "output_data"} # 'wrong_field' instead of 'result'
    mock_http_response = httpx.Response(
        status_code=200, 
        json=mock_response_json,
        request=httpx.Request("POST", f"{agent_url}/a2a/execute/{capability_name}")
    )
    mock_httpx_client.post.return_value = mock_http_response
    
    with pytest.raises(ValidationError) as excinfo:
        await a2a_client_adapter.execute_remote_capability(
            agent_url, capability_name, request_payload, response_model=MyTestResponse
        )
    
    # Check some details of the ValidationError if needed
    assert len(excinfo.value.errors()) == 1
    assert excinfo.value.errors()[0]['type'] == 'missing'
    assert excinfo.value.errors()[0]['loc'] == ('result',)
