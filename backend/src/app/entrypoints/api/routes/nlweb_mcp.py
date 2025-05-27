from typing import Any
from uuid import UUID
from pathlib import Path  # Added for proper path handling

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService

router = APIRouter(prefix="/tools", tags=["NLWeb & MCP"])


class NLWebAskRequest(BaseModel):
    """Request model for the /nlweb/ask endpoint."""

    query: str = Field(..., description="The natural language query")
    site: str | None = Field(None, description="Site context for the query")
    mode: str = Field("list", description="Query mode: list, summarize, or generate")
    streaming: bool = Field(True, description="Whether to enable streaming response")
    prev: str | None = Field(
        None, description="Comma-separated list of previous queries"
    )
    decontextualized_query: str | None = Field(
        None, description="Pre-decontextualized query"
    )
    query_id: str | None = Field(
        None, description="Query ID, auto-generated if not provided"
    )


class NLWebResult(BaseModel):
    """Individual result item in the response."""

    url: str
    name: str
    site: str
    score: float
    description: str
    schema_object: dict[str, Any]


class NLWebAskResponse(BaseModel):
    """Response model for the /nlweb/ask endpoint."""

    query_id: str
    results: list[NLWebResult]


def get_ai_pattern_execution_service() -> AIPatternExecutionService:
    """Dependency injection for AIPatternExecutionService."""
    # This will be replaced with proper DI container in production
    # For now, return a basic instance - the test mocks this anyway
    # Removed InMemoryConversationRepository import as UoW will provide it
    from app.service_layer.ai_provider_service import AIProviderService
    from app.service_layer.context_service import ContextService
    from app.service_layer.pattern_service import PatternService
    from app.service_layer.strategy_service import StrategyService
    from app.service_layer.template_service import TemplateService
    from app.service_layer.unit_of_work import FakeUnitOfWork

    # This is a simplified version - in production this would come from bootstrap
    # Provide a placeholder path for patterns_dir_path
    pattern_service = PatternService(patterns_dir_path=Path("data/patterns"))
    template_service = TemplateService()
    strategy_service = StrategyService()
    context_service = ContextService()
    ai_provider_service = AIProviderService()

    # uow now provides the conversation_repository
    uow = FakeUnitOfWork()

    return AIPatternExecutionService(
        pattern_service=pattern_service,
        template_service=template_service,
        strategy_service=strategy_service,
        context_service=context_service,
        ai_provider_service=ai_provider_service,
        uow=uow,
    )


@router.post("/nlweb/ask", response_model=NLWebAskResponse)
async def nlweb_ask(
    request: NLWebAskRequest,
    ai_service: AIPatternExecutionService = Depends(get_ai_pattern_execution_service),
) -> NLWebAskResponse:
    """
    Handle natural language queries and return structured results.

    This endpoint serves as a thin entrypoint that delegates to the service layer
    following the architectural pattern of keeping entrypoints minimal.
    """
    # Prepare input variables for the pattern execution
    input_variables: dict[str, Any] = {
        "query": request.query,
    }

    # Add optional parameters if provided
    if request.site:
        input_variables["site"] = request.site
    if request.mode:
        input_variables["mode"] = request.mode
    if request.streaming is not None:
        input_variables["streaming"] = request.streaming
    if request.prev:
        input_variables["prev"] = request.prev
    if request.decontextualized_query:
        input_variables["decontextualized_query"] = request.decontextualized_query

    session_id_uuid: UUID | None = None
    if request.query_id:
        try:
            session_id_uuid = UUID(request.query_id)
        except ValueError:
            # Handle invalid UUID string if necessary, e.g., return a 400 error
            # For now, we'll let it pass as None if invalid, or raise an error
            # Or, if query_id is not a valid UUID, it might mean it's a non-UUID session identifier
            # Depending on system design, this might need specific handling.
            # For strict UUID, a BadRequestError would be appropriate here.
            # Assuming query_id if present, should be a valid UUID string.
            pass  # Or raise HTTPException(status_code=400, detail="Invalid query_id format")

    # Execute the nlweb_ask_query pattern via the AI Pattern Execution Service
    # This follows the service layer pattern where business logic is orchestrated
    result = await ai_service.execute_pattern(
        pattern_name="nlweb_ask_query",
        input_variables=input_variables,
        session_id=session_id_uuid,  # Pass the converted UUID
    )

    # Transform the service layer result to the API response format
    # In a real implementation, this would involve proper result parsing
    return NLWebAskResponse(
        query_id=result.get("query_id", "generated-id"),
        results=[NLWebResult(**item) for item in result.get("results", [])],
    )


# @router.post("/mcp/execute")
# async def mcp_execute(): ...
