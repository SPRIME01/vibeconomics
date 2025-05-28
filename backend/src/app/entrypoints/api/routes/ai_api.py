from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.entrypoints.api.dependencies import get_ai_pattern_execution_service
from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService

ai_router = APIRouter()


class ExecutePatternRequest(BaseModel):
    pattern_name: str
    input_variables: dict[str, Any]
    session_id: str | None = None
    strategy_name: str | None = None
    context_name: str | None = None
    model_name: str | None = None


class ExecutePatternResponse(BaseModel):
    result: Any


@ai_router.post("/execute-pattern", response_model=ExecutePatternResponse)
async def execute_pattern(
    request: ExecutePatternRequest,
    ai_service: AIPatternExecutionService = Depends(get_ai_pattern_execution_service),
) -> ExecutePatternResponse:
    """Execute an AI pattern with the given parameters."""
    result = await ai_service.execute_pattern(
        pattern_name=request.pattern_name,
        input_variables=request.input_variables,
        session_id=request.session_id,
        strategy_name=request.strategy_name,
        context_name=request.context_name,
        model_name=request.model_name,
    )
    return ExecutePatternResponse(result=result)
