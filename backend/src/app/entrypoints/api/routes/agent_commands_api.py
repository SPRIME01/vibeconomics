from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from uuid import UUID
from typing import Dict, Any, Optional, Type

from pydantic import BaseModel, ValidationError # Added ValidationError
from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService, EmptyRenderedPromptError
from app.domain.agent.models import Conversation # Assuming Conversation might be part of a response or error detail

# Imports for actual dependencies of AIPatternExecutionService
from app.service_layer.pattern_service import PatternService
from app.service_layer.template_service import TemplateService
from app.service_layer.strategy_service import StrategyService
from app.service_layer.context_service import ContextService
from app.service_layer.ai_provider_service import AIProviderService
from app.domain.agent.ports import AbstractConversationRepository
from app.service_layer.unit_of_work import AbstractUnitOfWork

# Concrete implementations for abstract dependencies
from app.adapters.conversation_repository_inmemory import InMemoryConversationRepository
from app.adapters.uow_sqlmodel import SqlModelUnitOfWork # Using SqlModelUnitOfWork as found

router = APIRouter(prefix="/agent/commands", tags=["Agent Commands"])


class ExecutePatternRequest(BaseModel):
    pattern_name: str
    input_variables: Dict[str, Any]
    session_id: Optional[UUID] = None
    strategy_name: Optional[str] = None
    context_name: Optional[str] = None
    model_name: Optional[str] = None
    # output_model_name: Optional[str] = None # Omitted as per instructions


class ExecutePatternResponse(BaseModel):
    result: Any


async def get_aipes_service(
    pattern_service: PatternService = Depends(),
    template_service: TemplateService = Depends(),
    strategy_service: StrategyService = Depends(),
    context_service: ContextService = Depends(),
    ai_provider_service: AIProviderService = Depends(),
    # Provide concrete implementations for abstract types via Depends
    conversation_repository: AbstractConversationRepository = Depends(InMemoryConversationRepository),
    uow: AbstractUnitOfWork = Depends(SqlModelUnitOfWork) 
) -> AIPatternExecutionService:
    """
    Dependency provider for AIPatternExecutionService.
    Constructs and returns a real instance of AIPatternExecutionService
    with its required dependencies resolved by FastAPI.
    """
    return AIPatternExecutionService(
        pattern_service=pattern_service,
        template_service=template_service,
        strategy_service=strategy_service,
        context_service=context_service,
        ai_provider_service=ai_provider_service,
        conversation_repository=conversation_repository,
        uow=uow
    )


@router.post("/execute-pattern", response_model=ExecutePatternResponse)
async def execute_pattern_endpoint(
    request: ExecutePatternRequest,
    service: AIPatternExecutionService = Depends(get_aipes_service)
):
    try:
        service_response = await service.execute_pattern(
            pattern_name=request.pattern_name,
            input_variables=request.input_variables,
            session_id=request.session_id,
            strategy_name=request.strategy_name,
            context_name=request.context_name,
            model_name=request.model_name,
            output_model=None # API layer doesn't pass the Type[BaseModel] directly.
        )
        return ExecutePatternResponse(result=service_response)
    except EmptyRenderedPromptError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValidationError as e:
        # This handles Pydantic validation errors, e.g. from output_model parsing in the service
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Data validation or parsing error: {e}")
    except Exception as e:
        # In a real app, log the exception e with a logger
        # logger.error(f"An unexpected error occurred during pattern execution: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred.")
