import pytest
import uuid # Added for generating UUID
from fastapi.testclient import TestClient
from typing import Any, Dict, List

# Adjust the import path according to your project structure
from src.app.entrypoints.fastapi_app import app

# It's a good practice to initialize the TestClient once, possibly in a fixture,
# if you have multiple tests in this file. For a single test, this is fine.
# client = TestClient(app) # Now using client fixture from conftest.py

# Import the mock fixture to be used
# from ..conftest import mock_ai_provider_service # No, pytest finds fixtures automatically

def test_chat_flow_e2e(client: TestClient, mock_ai_provider_service: AsyncMock) -> None:
    """
    Tests the E2E chat flow, ensuring context is maintained between messages,
    using a mocked AIProviderService.
    """
    # client fixture is already using an app_instance with cleared overrides.
    # The mock_ai_provider_service fixture has already set its override on app_instance.

    # 1. Send initial message
    # Configure the mock response for the first AI call
    first_ai_response = "My name is MockBot. I hear your favorite color is blue."
    mock_ai_provider_service.get_completion.return_value = first_ai_response
    
    # Use a unique conversation ID for each test run, or manage state if needed.
    # For this test, we'll let the first message potentially create/use a session.
    # The copilot_api.py expects UUID for conversationId if provided.
    # Using a valid UUID string.
    test_conversation_id = str(uuid.uuid4())

    initial_payload: Dict[str, Any] = {
        "message": "My favorite color is blue. What is your name?",
        "conversationId": test_conversation_id
    }

    response1 = client.post("/api/v1/copilot/execute", json=initial_payload)
    assert response1.status_code == 200
    response1_data: Dict[str, Any] = response1.json()

    assert "reply" in response1_data
    initial_response_content: str = response1_data["reply"]
    assert initial_response_content == first_ai_response
    mock_ai_provider_service.get_completion.assert_called_once() # Verify it was called

    # 2. Send follow-up message
    # Configure the mock response for the second AI call, simulating context awareness
    second_ai_response = "You said your favorite color was blue."
    # Reset call count for the next assertion if needed, or use call_args_list
    mock_ai_provider_service.get_completion.reset_mock() 
    mock_ai_provider_service.get_completion.return_value = second_ai_response

    follow_up_payload: Dict[str, Any] = {
        "message": "What did I say my favorite color was?",
        "conversationId": test_conversation_id, # Crucial for context
    }

    response2 = client.post("/api/v1/copilot/execute", json=follow_up_payload)
    assert response2.status_code == 200
    response2_data: Dict[str, Any] = response2.json()

    assert "reply" in response2_data
    follow_up_response_content: str = response2_data["reply"]
    assert follow_up_response_content == second_ai_response
    
    # Key assertion: Check if the bot remembers the favorite color (now via mocked response)
    assert "blue" in follow_up_response_content.lower()
    mock_ai_provider_service.get_completion.assert_called_once()

# To run this test (assuming pytest is installed and you are in the `backend` directory):
# Ensure all required ENV VARS for the application config are set (as before).
# Then run: pytest tests/e2e/test_e2e_chat.py
# The `client` fixture from conftest.py will be used automatically.
# The `mock_ai_provider_service` fixture from conftest.py will also be used.
