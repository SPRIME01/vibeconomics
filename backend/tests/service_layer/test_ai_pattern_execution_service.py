import inspect
from unittest import mock

# Imports for new tests (moved up for PEP-8 compliance)
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import dspy
import httpx  # Ensure httpx is imported
import pytest
from pydantic import BaseModel, ValidationError

from app.adapters.a2a_client_adapter import A2AClientAdapter
from app.adapters.mem0_adapter import MemorySearchResult
from app.domain.agent.models import ChatMessage, Conversation
from app.service_layer.ai_pattern_execution_service import (
    AIPatternExecutionService,
    EmptyRenderedPromptError,
)
from app.service_layer.ai_provider_service import AIProviderService
from app.service_layer.context_service import ContextService
from app.service_layer.fabric_patterns import CollaborativeRAGModule
from app.service_layer.memory_service import AbstractMemoryService
from app.service_layer.pattern_service import PatternService
from app.service_layer.strategy_service import StrategyService
from app.service_layer.template_service import TemplateService
from app.service_layer.unit_of_work import AbstractUnitOfWork


@pytest.fixture
def mock_pattern_service() -> mock.Mock:
    return mock.Mock(spec=PatternService)


@pytest.fixture
def mock_template_service() -> mock.Mock:
    return mock.Mock(spec=TemplateService)


@pytest.fixture
def mock_strategy_service() -> mock.Mock:
    return mock.Mock(spec=StrategyService)


@pytest.fixture
def mock_context_service() -> mock.Mock:
    return mock.Mock(spec=ContextService)


@pytest.fixture
def mock_ai_provider_service() -> mock.Mock:
    return mock.Mock(spec=AIProviderService)


@pytest.fixture
def mock_memory_service() -> mock.Mock:
    return mock.Mock(spec=AbstractMemoryService)


@pytest.fixture
def mock_a2a_client_adapter():
    return AsyncMock()


@pytest.fixture
def mock_uow() -> mock.Mock:
    uow_mock = mock.Mock(spec=AbstractUnitOfWork)
    uow_mock.__aenter__ = mock.AsyncMock(return_value=uow_mock)
    uow_mock.__aexit__ = mock.AsyncMock(return_value=None)
    uow_mock.conversations = mock.Mock()
    uow_mock.conversations.get_by_id = mock.AsyncMock()
    uow_mock.conversations.create = mock.AsyncMock()
    uow_mock.conversations.save = mock.AsyncMock()
    uow_mock.commit = mock.AsyncMock()
    return uow_mock


# Imports for new tests


def test_aipatternexecutionservice_creation(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
    mock_memory_service: mock.Mock,
    mock_a2a_client_adapter: mock.Mock,
) -> None:
    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
        memory_service=mock_memory_service,
        a2a_client_adapter=mock_a2a_client_adapter,
    )
    assert service.pattern_service is mock_pattern_service
    assert service.template_service is mock_template_service
    assert service.strategy_service is mock_strategy_service
    assert service.context_service is mock_context_service
    assert service.ai_provider_service is mock_ai_provider_service
    assert service.uow is mock_uow
    assert service.memory_service is mock_memory_service
    assert service.a2a_client_adapter is mock_a2a_client_adapter


@pytest.mark.asyncio
async def test_execute_pattern_happy_path(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_pattern"
    input_variables = {"name": "TestUser"}
    strategy_name = "test_strategy"
    context_name = "test_context"
    model_name = "test_model"
    session_id = uuid4()

    mock_strategy = mock.Mock()
    mock_strategy.prompt = "Strategy: Think step-by-step."
    mock_context_content = "Context: Some context."
    mock_pattern_content = "Pattern: {{name}}"

    expected_base_prompt = "=== Strategy ===\nStrategy: Think step-by-step.\n\n=== Context ===\nContext: Some context.\n\n=== Current Task ===\nPattern: {{name}}"
    expected_rendered_prompt = "=== Strategy ===\nStrategy: Think step-by-step.\n\n=== Context ===\nContext: Some context.\n\n=== Current Task ===\nPattern: TestUser"
    expected_ai_response = "AI response here"

    mock_strategy_service.get_strategy = mock.AsyncMock(return_value=mock_strategy)
    mock_context_service.get_context_content = mock.AsyncMock(
        return_value=mock_context_content
    )
    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value=mock_pattern_content
    )
    mock_template_service.render = mock.AsyncMock(return_value=expected_rendered_prompt)
    mock_ai_provider_service.get_completion = mock.AsyncMock(
        return_value=expected_ai_response
    )
    mock_uow.conversations.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
    )

    # Act
    result = await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=session_id,
        strategy_name=strategy_name,
        context_name=context_name,
        model_name=model_name,
    )

    # Assert
    mock_strategy_service.get_strategy.assert_called_once_with(strategy_name)
    mock_context_service.get_context_content.assert_called_once_with(context_name)
    mock_pattern_service.get_pattern_content.assert_called_once_with(pattern_name)

    mock_template_service.render.assert_called_once_with(
        template=expected_base_prompt, variables=input_variables, context_data={}
    )
    mock_ai_provider_service.get_completion.assert_called_once_with(
        prompt=expected_rendered_prompt, model_name=model_name
    )
    assert result == expected_ai_response


@pytest.mark.asyncio
async def test_execute_pattern_creates_new_session(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_pattern"
    input_variables = {"query": "new session test"}
    expected_rendered_prompt = "=== Current Task ===\nUser query: new session test"
    expected_ai_response = "AI response for new session"

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value="User query: {{query}}"
    )
    mock_template_service.render = mock.AsyncMock(return_value=expected_rendered_prompt)
    mock_ai_provider_service.get_completion = mock.AsyncMock(
        return_value=expected_ai_response
    )
    mock_uow.conversations.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
    )

    # Act
    await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=None,
    )

    # Assert
    mock_uow.conversations.create.assert_called_once()
    args, _ = mock_uow.conversations.create.call_args
    created_conversation: Conversation = args[0]

    assert isinstance(created_conversation, Conversation)
    assert created_conversation.id is not None
    assert len(created_conversation.messages) == 2
    assert created_conversation.messages[0].role == "user"
    assert created_conversation.messages[0].content == "new session test"
    assert created_conversation.messages[1].role == "assistant"
    assert created_conversation.messages[1].content == expected_ai_response

    mock_uow.commit.assert_called()


@pytest.mark.asyncio
async def test_execute_pattern_loads_existing_session(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    session_id = uuid4()
    pattern_name = "test_pattern"
    input_variables = {"new_query": "follow up"}

    mock_existing_conversation = mock.Mock(spec=Conversation)
    mock_existing_conversation.id = session_id
    old_user_message = ChatMessage(role="user", content="Old message")
    old_assistant_message = ChatMessage(role="assistant", content="Old response")
    mock_existing_conversation.get_messages.return_value = [
        old_user_message,
        old_assistant_message,
    ]

    mock_uow.conversations.get_by_id.return_value = mock_existing_conversation

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value="Pattern: {{new_query}}"
    )
    expected_base_prompt = "=== Conversation History ===\nUSER: Old message\nASSISTANT: Old response\n=== End History ===\n\n=== Current Task ===\nPattern: {{new_query}}"
    rendered_prompt_from_template = "=== Conversation History ===\nUSER: Old message\nASSISTANT: Old response\n=== End History ===\n\n=== Current Task ===\nPattern: follow up"

    mock_template_service.render = mock.AsyncMock(
        return_value=rendered_prompt_from_template
    )
    expected_ai_response = "AI response to follow up"
    mock_ai_provider_service.get_completion = mock.AsyncMock(
        return_value=expected_ai_response
    )

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
    )

    # Act
    await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=session_id,
    )

    # Assert
    mock_uow.conversations.get_by_id.assert_called_once_with(session_id)

    mock_template_service.render.assert_called_once_with(
        template=expected_base_prompt, variables=input_variables, context_data={}
    )

    calls = [
        mock.call(role="user", content="follow up"),
        mock.call(role="assistant", content=expected_ai_response),
    ]
    mock_existing_conversation.add_message.assert_has_calls(calls, any_order=False)
    assert mock_existing_conversation.add_message.call_count == 2

    mock_uow.conversations.save.assert_called_once_with(mock_existing_conversation)
    mock_uow.commit.assert_called


@pytest.mark.asyncio
async def test_execute_pattern_uses_provided_session_id_for_new_conversation(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    provided_session_id = uuid4()
    pattern_name = "test_pattern"
    input_variables = {"data": "some data"}
    expected_rendered_prompt = "=== Current Task ===\nData: some data"
    expected_ai_response = "AI response for provided session ID"

    mock_uow.conversations.get_by_id.return_value = None

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value="Data: {{data}}"
    )
    mock_template_service.render = mock.AsyncMock(return_value=expected_rendered_prompt)
    mock_ai_provider_service.get_completion = mock.AsyncMock(
        return_value=expected_ai_response
    )

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
    )

    # Act
    await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=provided_session_id,
    )

    # Assert
    mock_uow.conversations.get_by_id.assert_called_once_with(provided_session_id)

    mock_uow.conversations.save.assert_called_once()
    mock_uow.conversations.create.assert_not_called()

    args, _ = mock_uow.conversations.save.call_args
    saved_conversation: Conversation = args[0]

    assert isinstance(saved_conversation, Conversation)
    assert saved_conversation.id == provided_session_id
    assert len(saved_conversation.messages) == 2
    assert saved_conversation.messages[0].role == "user"
    assert saved_conversation.messages[0].content == "some data"
    assert saved_conversation.messages[1].role == "assistant"
    assert saved_conversation.messages[1].content == expected_ai_response

    mock_uow.commit.assert_called


@pytest.mark.asyncio
async def test_execute_pattern_happy_path_no_strategy_no_context(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_pattern_simple"
    input_variables = {"item": "Widget"}
    model_name = "test_model_simple"

    mock_pattern_content = "Pattern: Describe {{item}}."
    expected_base_prompt = "=== Current Task ===\nPattern: Describe {{item}}."
    expected_rendered_prompt = "=== Current Task ===\nPattern: Describe Widget."
    expected_ai_response = "AI: A widget is a small gadget."

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value=mock_pattern_content
    )
    mock_template_service.render = mock.AsyncMock(return_value=expected_rendered_prompt)
    mock_ai_provider_service.get_completion = mock.AsyncMock(
        return_value=expected_ai_response
    )
    mock_uow.conversations.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
    )

    # Act
    result = await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=None,
        strategy_name=None,
        context_name=None,
        model_name=model_name,
    )

    # Assert
    mock_strategy_service.get_strategy.assert_not_called()
    mock_context_service.get_context_content.assert_not_called()

    mock_pattern_service.get_pattern_content.assert_called_once_with(pattern_name)
    mock_template_service.render.assert_called_once_with(
        template=expected_base_prompt, variables=input_variables, context_data={}
    )
    mock_ai_provider_service.get_completion.assert_called_once_with(
        prompt=expected_rendered_prompt, model_name=model_name
    )
    assert result == expected_ai_response


class MyTestOutputModel(BaseModel):
    name: str
    value: int


@pytest.mark.asyncio
async def test_execute_pattern_with_output_model_success(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_output_pattern"
    input_variables = {}
    ai_json_response = '{"name": "Test", "value": 123}'

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value="Some pattern"
    )
    mock_template_service.render = mock.AsyncMock(
        return_value="=== Current Task ===\nRendered prompt"
    )
    mock_ai_provider_service.get_completion = mock.AsyncMock(
        return_value=ai_json_response
    )
    mock_uow.conversations.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
    )

    # Act
    result = await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=None,
        output_model=MyTestOutputModel,
    )

    # Assert
    assert isinstance(result, MyTestOutputModel)
    assert result.name == "Test"
    assert result.value == 123


@pytest.mark.asyncio
async def test_execute_pattern_with_output_model_parsing_error(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_parsing_error_pattern"
    input_variables = {}
    invalid_ai_json_response = '{"name": "Test", "value": "not_an_int"}'

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value="Some pattern"
    )
    mock_template_service.render = mock.AsyncMock(
        return_value="=== Current Task ===\nRendered prompt"
    )
    mock_ai_provider_service.get_completion = mock.AsyncMock(
        return_value=invalid_ai_json_response
    )
    mock_uow.conversations.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
    )

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.execute_pattern(
            pattern_name=pattern_name,
            input_variables=input_variables,
            session_id=None,
            output_model=MyTestOutputModel,
        )


@pytest.mark.asyncio
async def test_execute_pattern_without_output_model_returns_raw_string(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_raw_string_pattern"
    input_variables = {}
    raw_response = "This is a raw string response."

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value="Some pattern"
    )
    mock_template_service.render = mock.AsyncMock(
        return_value="=== Current Task ===\nRendered prompt"
    )
    mock_ai_provider_service.get_completion = mock.AsyncMock(return_value=raw_response)
    mock_uow.conversations.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
    )

    # Act
    result = await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=None,
        output_model=None,
    )

    # Assert
    assert result == raw_response


@pytest.mark.asyncio
async def test_execute_pattern_with_simulated_template_extension(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "pattern_with_extension"
    input_variables = {"name": "TestUser"}
    model_name = "test_model_for_extension"

    mock_pattern_content = "Pattern with {{extension:some_extension:arg}} and {{name}}"
    expected_base_prompt = "=== Current Task ===\nPattern with {{extension:some_extension:arg}} and {{name}}"
    simulated_rendered_prompt_with_extension_output = (
        "=== Current Task ===\nPattern with EXTENSION_OUTPUT_HERE and TestUser"
    )
    expected_ai_response = "AI response based on extended prompt"

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value=mock_pattern_content
    )
    mock_template_service.render = mock.AsyncMock(
        return_value=simulated_rendered_prompt_with_extension_output
    )
    mock_ai_provider_service.get_completion = mock.AsyncMock(
        return_value=expected_ai_response
    )
    mock_uow.conversations.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
    )

    # Act
    result = await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=None,
        strategy_name=None,
        context_name=None,
        model_name=model_name,
    )

    # Assert
    mock_template_service.render.assert_called_once_with(
        template=expected_base_prompt, variables=input_variables, context_data={}
    )

    mock_ai_provider_service.get_completion.assert_called_once_with(
        prompt=simulated_rendered_prompt_with_extension_output, model_name=model_name
    )

    assert result == expected_ai_response
    mock_uow.conversations.create.assert_called_once()
    mock_uow.commit.assert_called


@pytest.mark.asyncio
async def test_execute_pattern_raises_error_on_empty_rendered_prompt(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_empty_prompt_pattern"
    input_variables = {}

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value="Some pattern content"
    )
    mock_template_service.render = mock.AsyncMock(return_value="")
    mock_uow.conversations.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
    )

    # Act & Assert
    with pytest.raises(
        EmptyRenderedPromptError,
        match="The prompt rendered from the template is empty or whitespace.",
    ):
        await service.execute_pattern(
            pattern_name=pattern_name,
            input_variables=input_variables,
            session_id=None,
        )

    mock_ai_provider_service.get_completion.assert_not_called()
    mock_uow.conversations.create.assert_not_called()
    mock_uow.conversations.save.assert_not_called()


@pytest.mark.asyncio
async def test_execute_pattern_raises_error_on_whitespace_rendered_prompt(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_whitespace_prompt_pattern"
    input_variables = {}

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value="Some pattern content"
    )
    mock_template_service.render = mock.AsyncMock(return_value="   ")
    mock_uow.conversations.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
    )

    # Act & Assert
    with pytest.raises(
        EmptyRenderedPromptError,
        match="The prompt rendered from the template is empty or whitespace.",
    ):
        await service.execute_pattern(
            pattern_name=pattern_name,
            input_variables=input_variables,
            session_id=None,
        )

    mock_ai_provider_service.get_completion.assert_not_called()
    mock_uow.conversations.create.assert_not_called()
    mock_uow.conversations.save.assert_not_called()


@pytest.mark.asyncio
async def test_execute_pattern_with_memory_service_available(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
    mock_memory_service: mock.Mock,
) -> None:
    # Arrange
    mock_memory_service.search.return_value = [
        MemorySearchResult(id="1", content="Memory content", score=0.9, metadata=None)
    ]

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value="Pattern with {{memory:search:user123:test query}}"
    )
    mock_template_service.render = mock.AsyncMock(
        return_value="Rendered prompt with memory results"
    )
    mock_ai_provider_service.get_completion = mock.AsyncMock(return_value="AI response")
    mock_uow.conversations.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
        memory_service=mock_memory_service,
    )

    # Act
    result = await service.execute_pattern(
        pattern_name="test_pattern",
        input_variables={"input": "test"},
    )

    # Assert
    assert result == "AI response"

    mock_template_service.render.assert_called_once()
    call_kwargs = mock_template_service.render.call_args[1]
    assert "context_data" in call_kwargs
    assert "memory_service" in call_kwargs["context_data"]
    assert call_kwargs["context_data"]["memory_service"] == mock_memory_service


@pytest.mark.asyncio
async def test_execute_pattern_with_a2a_client_adapter_available(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_uow: mock.Mock,
    mock_a2a_client_adapter: mock.Mock,
) -> None:
    # Arrange
    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value="Pattern with A2A integration"
    )
    mock_template_service.render = mock.AsyncMock(
        return_value="Rendered prompt with A2A results"
    )
    mock_ai_provider_service.get_completion = mock.AsyncMock(return_value="AI response")
    mock_uow.conversations.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
        a2a_client_adapter=mock_a2a_client_adapter,
    )

    # Act
    result = await service.execute_pattern(
        pattern_name="test_pattern",
        input_variables={"input": "test"},
    )

    # Assert
    assert result == "AI response"

    mock_template_service.render.assert_called_once()
    call_kwargs = mock_template_service.render.call_args[1]
    assert "context_data" in call_kwargs
    assert "a2a_client_adapter" in call_kwargs["context_data"]
    assert call_kwargs["context_data"]["a2a_client_adapter"] == mock_a2a_client_adapter


@pytest.mark.asyncio
async def test_execute_dspy_module_with_a2a_adapter(
    mock_pattern_service: MagicMock,
    mock_template_service: MagicMock,
    mock_strategy_service: MagicMock,
    mock_context_service: MagicMock,
    mock_ai_provider_service: MagicMock,
    mock_uow: MagicMock,
    mock_memory_service: MagicMock,
    mock_a2a_client_adapter: AsyncMock,
) -> None:
    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
        memory_service=mock_memory_service,
        a2a_client_adapter=mock_a2a_client_adapter,
    )

    # Create mock without spec to avoid signature validation issues
    MockDSPyModuleClass = MagicMock()
    mock_module_instance = MagicMock()
    mock_module_instance.forward = AsyncMock(return_value="mocked_dspy_output")
    MockDSPyModuleClass.return_value = mock_module_instance
    MockDSPyModuleClass.__name__ = "MockCollaborativeRAGModule"

    module_input_arg = "Test question for module"

    # Mock the __init__ signature to include a2a_adapter parameter
    mock_init_sig = MagicMock(spec=inspect.Signature)
    mock_a2a_param = MagicMock(spec=inspect.Parameter)
    mock_a2a_param.name = "a2a_adapter"
    mock_init_sig.parameters = {"a2a_adapter": mock_a2a_param}

    # Mock the forward signature to expect one argument (input_question) besides self
    mock_forward_sig = MagicMock(spec=inspect.Signature)
    mock_forward_param_self = MagicMock(spec=inspect.Parameter)
    mock_forward_param_self.name = "self"
    mock_forward_param_self.kind = inspect.Parameter.POSITIONAL_OR_KEYWORD
    mock_forward_param_input = MagicMock(spec=inspect.Parameter)
    mock_forward_param_input.name = "input_question"
    mock_forward_param_input.kind = inspect.Parameter.POSITIONAL_OR_KEYWORD
    mock_forward_sig.parameters = {
        "self": mock_forward_param_self,
        "input_question": mock_forward_param_input,
    }

    mock_dspy_lm = MagicMock()
    mock_settings = MagicMock()
    mock_settings.lm = mock_dspy_lm

    def signature_side_effect(obj):
        if obj == MockDSPyModuleClass.__init__:
            return mock_init_sig
        elif obj == MockDSPyModuleClass.forward or obj == mock_module_instance.forward:
            return mock_forward_sig
        else:
            raise ValueError(f"Unexpected object passed to inspect.signature: {obj}")

    with (
        patch.object(dspy, "settings", mock_settings),
        patch("inspect.signature", side_effect=signature_side_effect),
    ):
        result = await service.execute_dspy_module(
            module_class=MockDSPyModuleClass, module_input=module_input_arg
        )

    MockDSPyModuleClass.assert_called_once_with(a2a_adapter=mock_a2a_client_adapter)
    mock_module_instance.forward.assert_called_once_with(module_input_arg)
    assert result == "mocked_dspy_output"


# Define a simple DSPy module for the next test
class SimpleDSPyModule(dspy.Module):
    def __init__(self, an_arg: str = "default"):  # Does not take a2a_adapter
        super().__init__()
        self.an_arg = an_arg
        # Mock the predictor part if it involves an LM call for this simple module
        # For this test, we assume forward is simple or its LM interactions are not the focus.
        self.predictor = MagicMock()
        # Let's make predictor return a dspy.Prediction object
        self.predictor.return_value = dspy.Prediction(result="simple_output")

    async def forward(self, text_input: str) -> str:
        # Simulate some processing or a call to a sub-module/predictor
        # In a real module, this might be:
        # prediction = self.predictor(text_input=text_input)
        # return prediction.result
        # For the test, we can make it simpler if self.predictor is pre-configured:
        return self.predictor(text_input=text_input).result


@pytest.mark.asyncio
async def test_execute_dspy_module_without_a2a_adapter_if_not_needed(
    mock_pattern_service: MagicMock,
    mock_template_service: MagicMock,
    mock_strategy_service: MagicMock,
    mock_context_service: MagicMock,
    mock_ai_provider_service: MagicMock,
    mock_uow: MagicMock,
    mock_memory_service: MagicMock,
    mock_a2a_client_adapter: AsyncMock,
) -> None:
    mock_a2a_client_adapter.execute_remote_capability = AsyncMock()

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
        memory_service=mock_memory_service,
        a2a_client_adapter=mock_a2a_client_adapter,
    )

    module_input_val = "hello"
    constructor_kwarg_val = "custom_arg_value"

    mock_dspy_lm = MagicMock()
    mock_settings = MagicMock()
    mock_settings.lm = mock_dspy_lm
    with patch.object(dspy, "settings", mock_settings):
        # Create a simple mock module class that doesn't need a2a_adapter
        MockSimpleDSPyModule = MagicMock(name="MockSimpleDSPyModule")
        mock_simple_instance = MagicMock(name="mock_simple_instance")
        mock_simple_instance.forward = AsyncMock(
            return_value="simple_output_from_mocked_forward"
        )
        MockSimpleDSPyModule.return_value = mock_simple_instance

        # Mock the module's __init__ signature
        mock_init_sig = MagicMock(spec=inspect.Signature)
        mock_init_param_an_arg = MagicMock(spec=inspect.Parameter)
        mock_init_param_an_arg.name = "an_arg"
        mock_init_sig.parameters = {"an_arg": mock_init_param_an_arg}

        # Mock the module's forward signature
        mock_forward_sig = MagicMock(spec=inspect.Signature)
        mock_forward_param_self = MagicMock(spec=inspect.Parameter)
        mock_forward_param_self.name = "self"
        mock_forward_param_self.kind = inspect.Parameter.POSITIONAL_OR_KEYWORD
        mock_forward_param_text_input = MagicMock(spec=inspect.Parameter)
        mock_forward_param_text_input.name = "text_input"
        mock_forward_param_text_input.kind = inspect.Parameter.POSITIONAL_OR_KEYWORD
        mock_forward_sig.parameters = {
            "self": mock_forward_param_self,
            "text_input": mock_forward_param_text_input,
        }

        with patch("inspect.signature") as mock_inspect_signature:

            def signature_side_effect(obj):
                if obj == MockSimpleDSPyModule.__init__:
                    return mock_init_sig
                if (
                    hasattr(MockSimpleDSPyModule, "forward")
                    and obj == MockSimpleDSPyModule.forward
                ):
                    return mock_forward_sig
                if (
                    hasattr(mock_simple_instance, "forward")
                    and obj == mock_simple_instance.forward
                ):
                    return mock_forward_sig
                raise ValueError(
                    f"Unexpected object passed to inspect.signature: {obj}"
                )

            mock_inspect_signature.side_effect = signature_side_effect

            result = await service.execute_dspy_module(
                module_class=MockSimpleDSPyModule,
                module_input=module_input_val,
                an_arg=constructor_kwarg_val,
            )

        MockSimpleDSPyModule.assert_called_once_with(an_arg=constructor_kwarg_val)
        mock_simple_instance.forward.assert_called_once_with(module_input_val)
        assert result == "simple_output_from_mocked_forward"


@pytest.mark.asyncio
async def test_execute_dspy_module_raises_if_adapter_needed_but_missing(
    mock_pattern_service: MagicMock,
    mock_template_service: MagicMock,
    mock_strategy_service: MagicMock,
    mock_context_service: MagicMock,
    mock_ai_provider_service: MagicMock,
    mock_uow: MagicMock,
    mock_memory_service: MagicMock,
) -> None:
    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
        memory_service=mock_memory_service,
        a2a_client_adapter=None,
    )

    module_input_val = "Test question for error case"

    mock_dspy_lm = MagicMock()
    mock_settings = MagicMock()
    mock_settings.lm = mock_dspy_lm
    with patch.object(dspy, "settings", mock_settings):
        with pytest.raises(
            AttributeError,
            match=f"{CollaborativeRAGModule.__name__} requires an 'a2a_adapter'",
        ):
            await service.execute_dspy_module(
                module_class=CollaborativeRAGModule,
                module_input=module_input_val,
            )


@pytest.mark.asyncio
async def test_execute_pattern_propagates_a2a_extension_error(
    mock_pattern_service: MagicMock,
    mock_strategy_service: MagicMock,
    mock_context_service: MagicMock,
    mock_ai_provider_service: MagicMock,
    mock_uow: MagicMock,
    mock_memory_service: MagicMock,
) -> None:
    error_raising_a2a_adapter = AsyncMock(spec=A2AClientAdapter)
    mock_request = MagicMock(spec=httpx.Request)
    mock_request.method = "POST"
    mock_request.url = "http://test.agent/a2a"
    error_to_raise = httpx.RequestError("Simulated network error", request=mock_request)
    error_raising_a2a_adapter.execute_remote_capability.side_effect = error_to_raise

    real_template_service = TemplateService(
        memory_service=None,
        activepieces_adapter=None,
        a2a_client_adapter=error_raising_a2a_adapter,
    )

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=real_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        uow=mock_uow,
        memory_service=mock_memory_service,
        a2a_client_adapter=None,
    )

    pattern_name_for_test = "test_a2a_fail_pattern"
    # Use valid JSON for payload
    pattern_content_with_a2a = 'Calling A2A: {{a2a:invoke:agent_url=http://test.agent/a2a:capability=test_cap:payload={"key":"value"}}}'

    mock_pattern_service.get_pattern_content = mock.AsyncMock(
        return_value=pattern_content_with_a2a
    )

    mock_strategy_service.get_strategy = mock.AsyncMock(return_value=None)
    mock_context_service.get_context_content = mock.AsyncMock(return_value=None)
    mock_uow.conversations.get_by_id = mock.AsyncMock(return_value=None)

    with pytest.raises(httpx.RequestError, match="Simulated network error"):
        await service.execute_pattern(
            pattern_name=pattern_name_for_test,
            input_variables={"input": "test"},
        )

    error_raising_a2a_adapter.execute_remote_capability.assert_called_once()
    args, kwargs = error_raising_a2a_adapter.execute_remote_capability.call_args
    assert kwargs["agent_url"] == "http://test.agent/a2a"
    assert kwargs["capability_name"] == "test_cap"
    from app.service_layer.template_extensions import GenericRequestData

    assert isinstance(kwargs["request_payload"], GenericRequestData)
    assert kwargs["request_payload"].model_dump() == {"key": "value"}
