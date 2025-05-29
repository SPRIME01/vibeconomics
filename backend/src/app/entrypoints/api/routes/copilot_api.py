import asyncio
from uuid import UUID
from typing import Any, Dict # Added Dict and Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from app.entrypoints.api.dependencies import get_ai_pattern_execution_service
from app.service_layer.ai_pattern_execution_service import (
    AIPatternExecutionService,
    EmptyRenderedPromptError,
)

router = APIRouter()


# --- Pydantic Models ---
class CopilotExecuteRequest(BaseModel):
    """
    Request model for the /execute endpoint.
    Follows the typical structure expected by CopilotKit.
    """

    message: str  # Main message/query, can be used as default input if pattern_name/inputs not provided
    conversationId: str | None = None  # Can be UUID or any string ID from frontend
    pattern_name: str | None = None  # Optional: Name of the pattern to execute
    pattern_inputs: Dict[str, Any] | None = None  # Optional: Specific inputs for the pattern


class CopilotExecuteResponse(BaseModel):
    """
    Response model for the /execute endpoint.
    """

    reply: str
    # Potentially: conversationId, other metadata


class CopilotMockRequest(BaseModel):
    """
    Request model for the /mock endpoint.
    """

    scenario: str
    # ... any other params needed for mock


class CopilotMockResponse(BaseModel):
    """
    Response model for the /mock endpoint.
    """

    data: dict
    message: str


# --- Endpoints ---
@router.post("/execute", response_model=CopilotExecuteResponse)
async def execute_copilot_action(
    request_data: CopilotExecuteRequest,
    ai_service: AIPatternExecutionService = Depends(get_ai_pattern_execution_service),
):
    """
    Processes a CopilotKit frontend request by executing an AI pattern and returning the AI-generated reply.
    
    If both `pattern_name` and `pattern_inputs` are provided in the request, executes the specified pattern with the given inputs. Otherwise, defaults to the "conversational_chat" pattern using the provided message as input. Optionally uses `conversationId` to maintain conversational context if supplied and valid.
    
    Raises:
        HTTPException: If `conversationId` is not a valid UUID or if an error occurs during AI pattern execution.
    
    Returns:
        CopilotExecuteResponse: Contains the AI-generated reply as a string.
    """
    try:
        # Attempt to convert conversationId to UUID if it's provided
        session_id_uuid: UUID | None = None
        if request_data.conversationId:
            try:
                session_id_uuid = UUID(request_data.conversationId)
            except ValueError:
                # Explicitly return 400 for invalid UUID format
                raise HTTPException(
                    status_code=400,
                    detail="Invalid conversationId format. Must be a UUID.",
                )

        # Determine pattern_name and input_variables
        # Priority: 1. Explicit pattern_name/pattern_inputs from request
        #           2. Default to conversational_chat with message as input
        current_pattern_name: str
        current_input_variables: Dict[str, Any]

        if request_data.pattern_name and request_data.pattern_inputs is not None:
            current_pattern_name = request_data.pattern_name
            current_input_variables = request_data.pattern_inputs
        else:
            current_pattern_name = "conversational_chat"
            current_input_variables = {"input": request_data.message}
        
        result = await ai_service.execute_pattern(
            pattern_name=current_pattern_name,
            input_variables=current_input_variables,
            session_id=session_id_uuid,
            # model_name="gpt-4", # Optionally specify model, or let service use default
            # output_model=None # Define if structured output is expected
        )

        if isinstance(result, str):
            return CopilotExecuteResponse(reply=result)
        elif isinstance(result, BaseModel):  # Pydantic model
            # If the pattern returns a Pydantic model, decide how to represent it as 'reply'
            # For now, we'll convert its dict representation to a string.
            # This might need adjustment based on what CopilotKit frontend expects.
            return CopilotExecuteResponse(reply=str(result.model_dump()))
        else:
            # Fallback for other types
            return CopilotExecuteResponse(reply=str(result))

    except EmptyRenderedPromptError:
        # This specific error from AIPatternExecutionService indicates a configuration or template issue
        # that results in an empty prompt, which is a server-side problem.
        # Log this error for debugging.
        # logger.error(f"EmptyRenderedPromptError during Copilot action: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error: Failed to generate a valid AI prompt.",
        )
    except Exception as e:
        # Generic error handler for other exceptions from the service or other issues.
        # Log the exception details for server-side debugging.
        import logging

        logger = logging.getLogger("copilot_api")
        logger.error(f"Exception during Copilot action: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/mock", response_model=CopilotMockResponse)
async def mock_copilot_endpoint(request_data: CopilotMockRequest = Body(...)):
    """
    Mock endpoint for Storybook development and frontend testing.
    Returns predictable responses based on the 'scenario' parameter.
    This helps simulate various backend states without actual AI processing.

    Allowed scenarios:
    - **"success"**: Simulates a successful AI response.
    - **"error"**: Simulates a server-side error.
    - **"streaming"**: Simulates the beginning of a streaming response (actual streaming not implemented here).
    """
    scenario = request_data.scenario
    await asyncio.sleep(1)  # Simulate network and processing delay

    if scenario == "success":
        return CopilotMockResponse(
            data={"status": "ok", "conversationId": "mock-convo-123"},
            message="This is a successful mock response from the backend. The AI would typically provide a more insightful answer here.",
        )
    elif scenario == "error":
        return CopilotMockResponse(
            data={"status": "error", "error_code": "MOCK_SERVER_ERROR"},
            message="This is a simulated error response. The AI encountered an issue.",
        )
    elif scenario == "streaming":
        return CopilotMockResponse(
            data={
                "status": "streaming_session_started",
                "conversationId": "mock-convo-streaming-456",
            },
            message="This mock simulates the start of a streaming response. Further messages would follow.",
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario '{scenario}'. Allowed scenarios are: 'success', 'error', 'streaming'.",
        )


# Note: Router registration in main FastAPI app was handled in a previous step.
# CORS configuration is handled globally in `fastapi_app.py` based on `settings.all_cors_origins`.
# For Storybook (e.g., http://localhost:6006), ensure this list includes the origin
# or is permissive (e.g., ["*"] during development).
