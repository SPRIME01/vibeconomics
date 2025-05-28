import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Type

from pydantic import BaseModel

import dspy
from app.adapters.a2a_client_adapter import A2AClientAdapter
from app.service_layer.fabric_patterns import (
    CollaborativeRAGModule,
    RemoteTaskRequest,
    RemoteTaskResponse,
)


@pytest.mark.asyncio
async def test_fabric_collaborative_rag_pattern() -> None:
    """
    Asynchronously tests that CollaborativeRAGModule's forward method generates a query, invokes the remote capability via the adapter with correct parameters, and returns the expected combined output string.
    
    This test mocks the A2AClientAdapter and the generate_query method to simulate remote interaction and verifies that the forward method processes and formats the response as intended.
    """
    # a. Create a mock A2AClientAdapter
    mock_a2a_adapter = AsyncMock(spec=A2AClientAdapter)

    # b. Define the expected response from the mocked adapter
    # Note: The original subtask description for RemoteTaskResponse included a 'success' field.
    # However, the Pydantic model RemoteTaskResponse defined in the previous step
    # only has a 'data' field: class RemoteTaskResponse(BaseModel): data: str
    # Adjusting the mock response to match the actual Pydantic model.
    mock_remote_data = "mocked remote data from adapter"
    mock_remote_response_obj = RemoteTaskResponse(data=mock_remote_data)

    # c. Configure mock_a2a_adapter.execute_remote_capability
    # It's an async method, so it should be an AsyncMock
    mock_a2a_adapter.execute_remote_capability = AsyncMock(return_value=mock_remote_response_obj)

    # d. Instantiate CollaborativeRAGModule
    module_instance = CollaborativeRAGModule(a2a_adapter=mock_a2a_adapter)

    # e. Define a sample input question
    input_question: str = "What is the status of project X?"

    # f. Mock the dspy.Predict behavior for generate_query
    # The module's `forward` method calls `self.generate_query(input_question=input_question)`
    # This call returns a dspy.Prediction object (or a similar structure that has attributes).
    # The relevant attribute accessed is `query_for_remote_agent`.
    mock_generated_query_text: str = "Specific query details for project X"
    
    # Create a mock dspy.Prediction object (or a simple object that mimics its structure)
    # dspy.Prediction is basically a dotdict.
    # We can use MagicMock to simulate this structure easily.
    mock_prediction = MagicMock(spec=dspy.Prediction)
    mock_prediction.query_for_remote_agent = mock_generated_query_text
    
    # Patch the generate_query attribute of the module instance.
    # This attribute is an instance of dspy.Predict. We are mocking its __call__ method.
    module_instance.generate_query = MagicMock(return_value=mock_prediction)
    # If generate_query itself was async, we would use AsyncMock(return_value=mock_prediction)

    # g. Call await module_instance.forward(input_question=input_question)
    result: str = await module_instance.forward(input_question=input_question)

    # h. Assert that mock_a2a_adapter.execute_remote_capability was called once
    mock_a2a_adapter.execute_remote_capability.assert_called_once()

    # i. Retrieve the arguments with which execute_remote_capability was called
    call_args = mock_a2a_adapter.execute_remote_capability.call_args

    # j. Assert the call arguments
    assert call_args is not None, "execute_remote_capability was not called"
    
    # call_args is a tuple: (args, kwargs). We are interested in kwargs here as parameters are named.
    # Or, if they were passed positionally: args[0], args[1], etc.
    # Based on a2a_adapter.execute_remote_capability signature, they are keyword arguments.
    
    called_agent_url = call_args.kwargs.get("agent_url")
    called_capability_name = call_args.kwargs.get("capability_name")
    called_request_payload = call_args.kwargs.get("request_payload")
    called_response_model = call_args.kwargs.get("response_model")

    assert called_agent_url == "http://mocked-agent-url"
    assert called_capability_name == "remote_rag_task"

    assert isinstance(called_request_payload, RemoteTaskRequest), \
        f"Expected request_payload to be RemoteTaskRequest, got {type(called_request_payload)}"
    assert called_request_payload.task_details == mock_generated_query_text, \
        f"Expected task_details '{mock_generated_query_text}', got '{called_request_payload.task_details}'"

    assert called_response_model == RemoteTaskResponse, \
        f"Expected response_model to be RemoteTaskResponse, got {type(called_response_model)}"

    # k. Assert that the final output of the forward method is as expected
    expected_output: str = f"Input: {input_question}, Remote data: {mock_remote_data}"
    assert result == expected_output, \
        f"Expected output '{expected_output}', got '{result}'"

    # Also assert that the generate_query mock was called correctly
    module_instance.generate_query.assert_called_once_with(input_question=input_question)

# Example of how to run this test with pytest (not part of the file content):
# Ensure pytest and pytest-asyncio are installed:
# pip install pytest pytest-asyncio
# Then run:
# pytest backend/tests/service_layer/test_fabric_patterns.py
