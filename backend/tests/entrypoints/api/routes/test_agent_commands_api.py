import pytest
from unittest import mock
from uuid import UUID, uuid4

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from app.entrypoints.api.routes.agent_commands_api import router as agent_commands_router
# Import the placeholder dependency provider to override it
from app.entrypoints.api.routes.agent_commands_api import get_aipes_service
from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService, EmptyRenderedPromptError
from app.entrypoints.api.routes.agent_commands_api import ExecutePatternRequest # For type hinting if needed


# Setup TestClient with dependency override
# This mock will be used by the dependency override
mock_aipes_service_instance = mock.AsyncMock(spec=AIPatternExecutionService)

app = FastAPI()
app.include_router(agent_commands_router)

# This function will be used for the dependency override
def override_get_aipes_service_dependency():
    return mock_aipes_service_instance

app.dependency_overrides[get_aipes_service] = override_get_aipes_service_dependency

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mocks_before_each_test():
    """Reset mocks before each test."""
    mock_aipes_service_instance.reset_mock()
    # Specifically reset the main method we expect to be called
    mock_aipes_service_instance.execute_pattern.reset_mock(return_value=True, side_effect=None)


def test_execute_pattern_success():
    # Arrange
    expected_result = "AI result from service"
    mock_aipes_service_instance.execute_pattern.return_value = expected_result
    
    session_uuid = uuid4()
    request_payload = {
        "pattern_name": "test_pattern",
        "input_variables": {"key": "value"},
        "session_id": str(session_uuid),
        "strategy_name": "test_strategy",
        "context_name": "test_context",
        "model_name": "test_model"
    }

    # Act
    response = client.post("/agent/commands/execute-pattern", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"result": expected_result}
    
    mock_aipes_service_instance.execute_pattern.assert_called_once_with(
        pattern_name=request_payload["pattern_name"],
        input_variables=request_payload["input_variables"],
        session_id=session_uuid, # Compare with UUID object
        strategy_name=request_payload["strategy_name"],
        context_name=request_payload["context_name"],
        model_name=request_payload["model_name"],
        output_model=None
    )

def test_execute_pattern_missing_pattern_name():
    # Arrange
    request_payload = {
        # "pattern_name": "test_pattern", # Missing
        "input_variables": {"key": "value"}
    }

    # Act
    response = client.post("/agent/commands/execute-pattern", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_json = response.json()
    # Check for the specific error related to 'pattern_name' being missing
    assert any(
        err["type"] == "missing" and err["loc"] == ["body", "pattern_name"] 
        for err in response_json["detail"]
    )

def test_execute_pattern_service_generic_exception():
    # Arrange
    error_message = "A generic service error occurred"
    mock_aipes_service_instance.execute_pattern.side_effect = Exception(error_message)
    
    request_payload = {
        "pattern_name": "test_pattern_generic_error",
        "input_variables": {"key": "value"}
    }

    # Act
    response = client.post("/agent/commands/execute-pattern", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    # The endpoint currently returns a generic message for Exception, not the specific error message.
    assert response.json()["detail"] == "An internal server error occurred."

def test_execute_pattern_service_empty_prompt_error():
    # Arrange
    error_message = "Rendered prompt is empty or whitespace." # Exact message from service
    mock_aipes_service_instance.execute_pattern.side_effect = EmptyRenderedPromptError(error_message)
    
    request_payload = {
        "pattern_name": "test_pattern_empty_prompt",
        "input_variables": {"key": "value"}
    }

    # Act
    response = client.post("/agent/commands/execute-pattern", json=request_payload)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == error_message
