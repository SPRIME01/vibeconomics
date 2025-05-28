import asyncio
import asyncio
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService, EmptyRenderedPromptError
from app.entrypoints.api.dependencies import get_ai_pattern_execution_service

router = APIRouter()

# --- Pydantic Models ---
class CopilotExecuteRequest(BaseModel):
    """
    Request model for the /execute endpoint.
    Follows the typical structure expected by CopilotKit.
    """
    message: str
    conversationId: str | None = None # Can be UUID or any string ID from frontend
    # Potentially: user_id, context_variables, etc.

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
    ai_service: AIPatternExecutionService = Depends(get_ai_pattern_execution_service)
):
    """
    Receives a request from a CopilotKit frontend, processes it
    using the AIPatternExecutionService, and returns the AI's response.

    The `conversationId` can be used to maintain context across multiple turns
    if the `AIPatternExecutionService` is configured to use it (e.g., via session_id).
    """
    try:
        # Attempt to convert conversationId to UUID if it's provided
        session_id_uuid: UUID | None = None
        if request_data.conversationId:
            try:
                session_id_uuid = UUID(request_data.conversationId)
            except ValueError:
                # Handle cases where conversationId is not a valid UUID if necessary
                # For now, we'll proceed with None, or you could raise a 400 error
                # raise HTTPException(status_code=400, detail="Invalid conversationId format. Must be a UUID.")
                pass # Or log a warning, depending on desired strictness

        # Using a generic pattern name for now. This should be defined in your pattern service.
        # The input variables are passed directly from the request.
        result = await ai_service.execute_pattern(
            pattern_name="copilot_chat", # Replace with an actual, defined pattern
            input_variables={"message": request_data.message},
            session_id=session_id_uuid,
            # model_name="gpt-4", # Optionally specify model, or let service use default
            # output_model=None # Define if structured output is expected
        )
        
        if isinstance(result, str):
            return CopilotExecuteResponse(reply=result)
        elif hasattr(result, 'model_dump'): # Pydantic model
            # If the pattern returns a Pydantic model, decide how to represent it as 'reply'
            # For now, we'll convert its dict representation to a string.
            # This might need adjustment based on what CopilotKit frontend expects.
            return CopilotExecuteResponse(reply=str(result.model_dump()))
        else:
            # Fallback for other types
            return CopilotExecuteResponse(reply=str(result))

    except EmptyRenderedPromptError as e:
        # This specific error from AIPatternExecutionService indicates a configuration or template issue
        # that results in an empty prompt, which is a server-side problem.
        # Log this error for debugging.
        # logger.error(f"EmptyRenderedPromptError during Copilot action: {e}")
        raise HTTPException(status_code=500, detail="Internal server error: Failed to generate a valid AI prompt.")
    except Exception as e:
        # Generic error handler for other exceptions from the service or other issues.
        # Log the exception details for server-side debugging.
        # logger.error(f"Exception during Copilot action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.post("/mock", response_model=CopilotMockResponse)
async def mock_copilot_endpoint(request_data: CopilotMockRequest):
    """
    Mock endpoint for Storybook development and testing.
    Returns predictable responses based on the 'scenario' parameter.
    """
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
    await asyncio.sleep(1) # Simulate network and processing delay

    if scenario == "success":
        return CopilotMockResponse(
            data={"status": "ok", "conversationId": "mock-convo-123"}, 
            message="This is a successful mock response from the backend. The AI would typically provide a more insightful answer here."
        )
    elif scenario == "error":
        # To properly test frontend error handling, it's often better to raise an HTTPException
        # that the frontend will receive as a non-2xx response.
        # However, the requirement was to return a JSON structure for "error".
        # If actual HTTP error testing is needed, this could be changed to:
        # raise HTTPException(status_code=500, detail="This is a simulated server error.")
        return CopilotMockResponse(
            data={"status": "error", "error_code": "MOCK_SERVER_ERROR"}, 
            message="This is a simulated error response. The AI encountered an issue."
        )
    elif scenario == "streaming":
        # Actual streaming would involve returning a StreamingResponse.
        # For this mock, we just indicate that streaming would occur.
        return CopilotMockResponse(
            data={"status": "streaming_session_started", "conversationId": "mock-convo-streaming-456"},
            message="This mock simulates the start of a streaming response. Further messages would follow."
        )
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid scenario '{scenario}'. Allowed scenarios are: 'success', 'error', 'streaming'."
        )

# Note: Router registration in main FastAPI app was handled in a previous step.
# CORS configuration is handled globally in `fastapi_app.py` based on `settings.all_cors_origins`.
# For Storybook (e.g., http://localhost:6006), ensure this list includes the origin
# or is permissive (e.g., ["*"] during development).
