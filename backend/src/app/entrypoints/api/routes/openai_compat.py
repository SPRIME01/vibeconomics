import time  # For timestamp
import uuid  # For generating request IDs if not provided

from fastapi import APIRouter, Body, HTTPException, status
from pydantic import BaseModel, Field  # BaseModel moved here, Field confirmed

# from app.service_layer.message_bus import AbstractMessageBus # For command bus via DI
# from app.service_layer.commands.chat_commands import ProcessUserChatMessageCommand # Example command
# from app.entrypoints.api.dependencies import MessageBusDep # If using a command bus pattern via message bus

router = APIRouter(prefix="/v1", tags=["OpenAI Compatible Endpoints"])


class ChatMessage(BaseModel):
    role: str
    content: str | None = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float | None = 1.0
    top_p: float | None = 1.0
    n: int | None = 1
    stream: bool | None = False
    stop: str | list[str] | None = None
    max_tokens: int | None = None
    presence_penalty: float | None = 0
    frequency_penalty: float | None = 0
    logit_bias: dict[str, float] | None = None
    user: str | None = None
    request_id: str | None = Field(default_factory=lambda: str(uuid.uuid4()))


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[ChatCompletionChoice]


async def dispatch_chat_command(
    request: ChatCompletionRequest,
) -> ChatCompletionResponse:
    if request.model == "dspy-model":
        response_message_content = (
            "Mocked DSPy response to: " + request.messages[-1].content
            if request.messages and request.messages[-1].content
            else "Mocked DSPy response."
        )

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant", content=response_message_content
                    ),
                )
            ],
        )
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4()}",
        model=request.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content="Generic mock response."),
            )
        ],
    )


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest = Body(...),
) -> ChatCompletionResponse:
    if request.stream and request.stream is True:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Streaming responses are not yet implemented.",
        )
    if not request.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Messages list cannot be empty.",
        )
    response_data = await dispatch_chat_command(request)
    return response_data
