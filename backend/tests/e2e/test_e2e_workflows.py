import pytest
import uuid
import httpx # For A2AClientAdapter constructor
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock 
from typing import Any, Dict, Type # Added Type

# FastAPI app instance
from src.app.entrypoints.fastapi_app import app
# The class we want to mock and its dependency provider
from src.app.adapters.a2a_client_adapter import A2AClientAdapter
from src.app.entrypoints.api.dependencies import get_a2a_client_adapter
# Import Pydantic BaseModel for type hinting request_payload if it's a specific dynamic model
from pydantic import BaseModel


@pytest.mark.asyncio
async def test_e2e_delegated_research_workflow_with_mocked_a2a() -> None:
    """
    Tests the E2E 'delegated_research_and_summarize' workflow, mocking the external A2A communication
    by overriding the A2AClientAdapter dependency.
    """
    
    mocked_web_search_response: Dict[str, Any] = {
        "raw_search_data": "Lots of web results for 'fastapi performance'. Result 1, Result 2."
    }
    mocked_key_points_response: Dict[str, Any] = {
        "key_points": [
            "FastAPI is known for high performance.",
            "It uses Starlette and Pydantic for speed.",
            "Async support is a key factor.",
        ]
    }

    async def mock_execute_remote_capability_side_effect(
        agent_url: str,
        capability_name: str,
        request_payload: BaseModel, # The dynamically created Pydantic model
        response_model: Any | None = None,
    ) -> Dict[str, Any]:
        if "websearch.agent" in agent_url and capability_name == "perform_search":
            # request_payload here will be a Pydantic model with a 'query' field
            assert hasattr(request_payload, "query")
            assert request_payload.query == "fastapi performance"
            return mocked_web_search_response
        elif "dataanalysis.agent" in agent_url and capability_name == "extract_key_points":
            # request_payload here will be a Pydantic model with a 'data' field.
            # The value of 'data' will be the result of the previous call (mocked_web_search_response)
            assert hasattr(request_payload, "data")
            # request_payload.data should be the dictionary mocked_web_search_response
            assert request_payload.data == mocked_web_search_response 
            assert "lots of web results" in request_payload.data["raw_search_data"].lower()
            return mocked_key_points_response
        
        pytest.fail(f"Unexpected A2A call to {agent_url}/{capability_name}")
        return {}

    mock_http_client = MagicMock(spec=httpx.AsyncClient)
    mock_adapter_instance = A2AClientAdapter(http_client=mock_http_client)
    
    mock_adapter_instance.execute_remote_capability = AsyncMock(
        side_effect=mock_execute_remote_capability_side_effect
    )

    app.dependency_overrides[get_a2a_client_adapter] = lambda: mock_adapter_instance

    client = TestClient(app)

    test_topic = "fastapi performance"
    payload = {
        "message": f"Please research and summarize {test_topic}",
        "conversationId": str(uuid.uuid4()),
        "pattern_name": "delegated_research_and_summarize",
        "pattern_inputs": {"input_query": test_topic}
    }

    response = client.post("/api/v1/copilot/execute", json=payload)

    assert response.status_code == 200, f"Response content: {response.text}"
    response_data = response.json()
    assert "reply" in response_data

    assert mock_adapter_instance.execute_remote_capability.call_count == 2

    call_args_list = mock_adapter_instance.execute_remote_capability.call_args_list
    
    # First call (web search)
    args_call1, kwargs_call1 = call_args_list[0]
    assert "http://websearch.agent/a2a" == kwargs_call1['agent_url']
    assert "perform_search" == kwargs_call1['capability_name']
    assert test_topic == kwargs_call1['request_payload'].query 

    # Second call (extract key points)
    args_call2, kwargs_call2 = call_args_list[1]
    assert "http://dataanalysis.agent/a2a" == kwargs_call2['agent_url']
    assert "extract_key_points" == kwargs_call2['capability_name']
    assert mocked_web_search_response == kwargs_call2['request_payload'].data
        
    final_reply = response_data["reply"].lower()
    assert "fastapi is known for high performance" in final_reply
    assert "starlette and pydantic" in final_reply
    assert "async support" in final_reply
    assert test_topic.split(" ")[0] in final_reply

    app.dependency_overrides.clear()
