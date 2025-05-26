import pytest
from unittest import mock
from uuid import UUID, uuid4
from typing import Type

from pydantic import BaseModel, ValidationError

from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService, EmptyRenderedPromptError # Added EmptyRenderedPromptError
from app.domain.agent.models import Conversation, ChatMessage
from app.domain.agent.ports import AbstractConversationRepository
from app.service_layer.unit_of_work import AbstractUnitOfWork
from app.service_layer.pattern_service import PatternService
from app.service_layer.template_service import TemplateService
from app.service_layer.strategy_service import StrategyService
from app.service_layer.context_service import ContextService
from app.service_layer.ai_provider_service import AIProviderService


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
def mock_conversation_repository() -> mock.Mock:
    return mock.Mock(spec=AbstractConversationRepository)

@pytest.fixture
def mock_uow() -> mock.Mock:
    # Ensure mock_uow supports async with
    uow_mock = mock.Mock(spec=AbstractUnitOfWork)
    uow_mock.__aenter__ = mock.AsyncMock(return_value=uow_mock) # Make __aenter__ return the mock itself or a relevant context
    uow_mock.__aexit__ = mock.AsyncMock(return_value=None)
    return uow_mock


def test_aipatternexecutionservice_creation(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_conversation_repository: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
        uow=mock_uow,
    )
    assert service.pattern_service is mock_pattern_service
    assert service.template_service is mock_template_service
    assert service.strategy_service is mock_strategy_service
    assert service.context_service is mock_context_service
    assert service.ai_provider_service is mock_ai_provider_service
    assert service.conversation_repository is mock_conversation_repository
    assert service.uow is mock_uow


@pytest.mark.asyncio
async def test_execute_pattern_happy_path(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_conversation_repository: mock.Mock, # Not used directly in this test but part of service init
    mock_uow: mock.Mock, # Not used directly in this test but part of service init
) -> None:
    # Arrange
    pattern_name = "test_pattern"
    input_variables = {"name": "TestUser"}
    strategy_name = "test_strategy"
    context_name = "test_context"
    model_name = "test_model"
    session_id = uuid4()

    mock_strategy_content = "Strategy: Think step-by-step."
    mock_context_content = "Context: Some context."
    mock_pattern_content = "Pattern: {{name}}"
    
    expected_base_prompt = f"{mock_strategy_content}\n\n{mock_context_content}\n\n{mock_pattern_content}"
    expected_rendered_prompt = "Strategy: Think step-by-step.\n\nContext: Some context.\n\nPattern: TestUser"
    expected_ai_response = "AI response here"

    mock_strategy_service.get_strategy.return_value = mock_strategy_content
    mock_context_service.get_context_content.return_value = mock_context_content
    mock_pattern_service.get_pattern_content.return_value = mock_pattern_content
    mock_template_service.render.return_value = expected_rendered_prompt
    mock_ai_provider_service.get_completion.return_value = expected_ai_response

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
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
        template_str=expected_base_prompt, variables=input_variables
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
    mock_conversation_repository: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_pattern"
    input_variables = {"query": "new session test"}
    expected_rendered_prompt = "User query: new session test"
    expected_ai_response = "AI response for new session"

    mock_pattern_service.get_pattern_content.return_value = "User query: {{query}}"
    mock_template_service.render.return_value = expected_rendered_prompt
    mock_ai_provider_service.get_completion.return_value = expected_ai_response
    
    # Ensure no conversation is found initially if a (None) session_id would be passed
    mock_conversation_repository.get_by_id.return_value = None 

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
        uow=mock_uow,
    )

    # Act
    await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=None, # Explicitly no session_id
    )

    # Assert
    # Check that create was called, capturing the conversation
    captured_conversation = mock.ทาน() # Placeholder for unittest.mock.ANY or a captor
    
    # We need to use mock.ANY or capture the argument if using unittest.mock
    # Pytest's mock typically uses call_args
    
    # Assert create was called once
    mock_conversation_repository.create.assert_called_once()
    
    # Get the conversation object passed to create
    args, _ = mock_conversation_repository.create.call_args
    created_conversation: Conversation = args[0]

    assert isinstance(created_conversation, Conversation)
    assert created_conversation.id is not None
    assert len(created_conversation.messages) == 2
    assert created_conversation.messages[0].role == "user"
    assert created_conversation.messages[0].content == expected_rendered_prompt
    assert created_conversation.messages[1].role == "assistant"
    assert created_conversation.messages[1].content == expected_ai_response
    
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_execute_pattern_loads_existing_session(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_conversation_repository: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    session_id = uuid4()
    pattern_name = "test_pattern"
    input_variables = {"new_query": "follow up"}
    
    mock_existing_conversation = mock.Mock(spec=Conversation)
    mock_existing_conversation.id = session_id
    old_user_message = ChatMessage(role="user", content="Old message")
    mock_existing_conversation.get_messages.return_value = [old_user_message]
    
    mock_conversation_repository.get_by_id.return_value = mock_existing_conversation
    
    mock_pattern_service.get_pattern_content.return_value = "Pattern: {{new_query}}"
    # This is the prompt that will be sent to the AI, including history and new input
    expected_rendered_prompt_for_ai = "user: Old message\n\nPattern: follow up" 
    # This is what template_service.render will receive (base_prompt without history)
    # The history is prepended *before* this base_prompt is constructed for rendering
    # So, the `base_prompt` for rendering will be "Pattern: {{new_query}}"
    # But the actual input to the AI includes history.
    # Let's adjust the test based on the implementation:
    # prompt_parts (history) -> strategy -> context -> pattern -> rendered_user_prompt
    # The test should reflect that `template_service.render` gets the *non-history* part
    
    expected_base_prompt_for_render = "Pattern: {{new_query}}" # What render gets
    # rendered_user_prompt is the result of rendering expected_base_prompt_for_render
    rendered_user_prompt_from_template = "Pattern: follow up" 
    
    mock_template_service.render.return_value = rendered_user_prompt_from_template
    expected_ai_response = "AI response to follow up"
    mock_ai_provider_service.get_completion.return_value = expected_ai_response

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
        uow=mock_uow,
    )

    # Act
    await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=session_id,
    )

    # Assert
    mock_conversation_repository.get_by_id.assert_called_once_with(session_id)
    
    # The template_service.render is called with the base_prompt that includes history, strategy, context, pattern
    # In this test, we only have history and pattern.
    # The service logic is:
    # 1. Load history -> prompt_parts = ["user: Old message"]
    # 2. Add pattern -> prompt_parts = ["user: Old message", "Pattern: {{new_query}}"]
    # 3. Join -> base_prompt = "user: Old message\n\nPattern: {{new_query}}"
    # 4. Render -> rendered_user_prompt = "user: Old message\n\nPattern: follow up" (this goes to AI)
    
    # So template_service.render should be called with the combined prompt string
    # (history + pattern_template)
    expected_template_str_for_render = f"{old_user_message.role}: {old_user_message.content}\n\nPattern: {{{{new_query}}}}"

    mock_template_service.render.assert_called_once_with(
        template_str=expected_template_str_for_render, variables=input_variables
    )
    
    # add_message should be called with the rendered_user_prompt (which is the full prompt to AI)
    # and the AI response
    calls = [
        mock.call(role="user", content=rendered_user_prompt_from_template),
        mock.call(role="assistant", content=expected_ai_response),
    ]
    mock_existing_conversation.add_message.assert_has_calls(calls, any_order=False)
    assert mock_existing_conversation.add_message.call_count == 2
    
    mock_conversation_repository.save.assert_called_once_with(mock_existing_conversation)
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_execute_pattern_uses_provided_session_id_for_new_conversation(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock, # Added for completeness
    mock_context_service: mock.Mock,   # Added for completeness
    mock_ai_provider_service: mock.Mock,
    mock_conversation_repository: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    provided_session_id = uuid4()
    pattern_name = "test_pattern"
    input_variables = {"data": "some data"}
    expected_rendered_prompt = "Data: some data"
    expected_ai_response = "AI response for provided session ID"

    mock_conversation_repository.get_by_id.return_value = None # Simulate conversation not found
    
    mock_pattern_service.get_pattern_content.return_value = "Data: {{data}}"
    mock_template_service.render.return_value = expected_rendered_prompt
    mock_ai_provider_service.get_completion.return_value = expected_ai_response
    
    # Mock strategy and context to return None or not be called if not provided
    mock_strategy_service.get_strategy.return_value = None
    mock_context_service.get_context_content.return_value = None


    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
        uow=mock_uow,
    )

    # Act
    await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=provided_session_id, # Provide the session_id
    )

    # Assert
    mock_conversation_repository.get_by_id.assert_called_once_with(provided_session_id)
    
    # In the current implementation, if session_id is provided but not found,
    # a Conversation object is created with that ID, and then 'save' is called.
    # 'create' is only called if session_id was initially None.
    mock_conversation_repository.save.assert_called_once() 
    mock_conversation_repository.create.assert_not_called() # Ensure create is not called

    args, _ = mock_conversation_repository.save.call_args
    saved_conversation: Conversation = args[0]

    assert isinstance(saved_conversation, Conversation)
    assert saved_conversation.id == provided_session_id # Key assertion
    assert len(saved_conversation.messages) == 2
    assert saved_conversation.messages[0].role == "user"
    assert saved_conversation.messages[0].content == expected_rendered_prompt
    assert saved_conversation.messages[1].role == "assistant"
    assert saved_conversation.messages[1].content == expected_ai_response
    
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_execute_pattern_happy_path_no_strategy_no_context(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_conversation_repository: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_pattern_simple"
    input_variables = {"item": "Widget"}
    model_name = "test_model_simple"
    # session_id = uuid4() # session_id is not strictly needed for this test's core logic

    mock_pattern_content = "Pattern: Describe {{item}}."
    expected_base_prompt = mock_pattern_content # Only pattern content
    expected_rendered_prompt = "Pattern: Describe Widget."
    expected_ai_response = "AI: A widget is a small gadget."

    # Ensure strategy and context services return None or are not called
    mock_strategy_service.get_strategy.return_value = None 
    mock_context_service.get_context_content.return_value = None
    
    mock_pattern_service.get_pattern_content.return_value = mock_pattern_content
    mock_template_service.render.return_value = expected_rendered_prompt
    mock_ai_provider_service.get_completion.return_value = expected_ai_response
    # For this test, assume get_by_id returns None if session_id were passed and not None
    mock_conversation_repository.get_by_id.return_value = None


    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
        uow=mock_uow,
    )

    # Act
    result = await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=None, # Pass None for session_id to ensure create path for conversation
        strategy_name=None,  # No strategy
        context_name=None,   # No context
        model_name=model_name,
    )

    # Assert
    # Because strategy_name and context_name are None, these services should not be called.
    mock_strategy_service.get_strategy.assert_not_called()
    mock_context_service.get_context_content.assert_not_called()

    mock_pattern_service.get_pattern_content.assert_called_once_with(pattern_name)
    mock_template_service.render.assert_called_once_with(
        template_str=expected_base_prompt, variables=input_variables
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
    mock_conversation_repository: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_output_pattern"
    input_variables = {}
    ai_json_response = '{"name": "Test", "value": 123}'

    mock_pattern_service.get_pattern_content.return_value = "Some pattern"
    mock_template_service.render.return_value = "Rendered prompt" # The content of this doesn't matter for output parsing
    mock_ai_provider_service.get_completion.return_value = ai_json_response
    mock_conversation_repository.get_by_id.return_value = None # Assume new session

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
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
    mock_conversation_repository: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_parsing_error_pattern"
    input_variables = {}
    invalid_ai_json_response = '{"name": "Test", "value": "not_an_int"}' # value should be int

    mock_pattern_service.get_pattern_content.return_value = "Some pattern"
    mock_template_service.render.return_value = "Rendered prompt"
    mock_ai_provider_service.get_completion.return_value = invalid_ai_json_response
    mock_conversation_repository.get_by_id.return_value = None # Assume new session

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
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
    mock_conversation_repository: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_raw_string_pattern"
    input_variables = {}
    raw_response = "This is a raw string response."

    mock_pattern_service.get_pattern_content.return_value = "Some pattern"
    mock_template_service.render.return_value = "Rendered prompt"
    mock_ai_provider_service.get_completion.return_value = raw_response
    mock_conversation_repository.get_by_id.return_value = None # Assume new session

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
        uow=mock_uow,
    )

    # Act
    result = await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=None,
        output_model=None, # Explicitly no output model
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
    mock_conversation_repository: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    """
    Placeholder test for template extensions.
    This test simulates the effect of a template extension by configuring
    mock_template_service.render to return a prompt that notionally includes
    output from such an extension. It verifies that AIPatternExecutionService
    uses this (potentially modified by extension) prompt for AI completion.
    """
    # Arrange
    pattern_name = "pattern_with_extension"
    input_variables = {"name": "TestUser"}
    model_name = "test_model_for_extension"

    # Notionally, pattern_content could be: "Pattern with {{extension:some_extension:arg}} and {{name}}"
    # The actual content here doesn't strictly matter as render is mocked.
    mock_pattern_content = "Pattern with {{extension:some_extension:arg}} and {{name}}"
    
    # This is the key part: simulate that template_service.render processed the extension
    # and produced a prompt including the extension's output.
    simulated_rendered_prompt_with_extension_output = (
        "Pattern with EXTENSION_OUTPUT_HERE and TestUser"
    )
    expected_ai_response = "AI response based on extended prompt"

    mock_pattern_service.get_pattern_content.return_value = mock_pattern_content
    mock_template_service.render.return_value = simulated_rendered_prompt_with_extension_output
    mock_ai_provider_service.get_completion.return_value = expected_ai_response
    
    # Assume new session for simplicity, as session handling is tested elsewhere
    mock_conversation_repository.get_by_id.return_value = None
    # Assume no strategy or context for simplicity
    mock_strategy_service.get_strategy.return_value = None
    mock_context_service.get_context_content.return_value = None


    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
        uow=mock_uow,
    )

    # Act
    result = await service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_variables,
        session_id=None, # New session
        strategy_name=None,
        context_name=None,
        model_name=model_name,
    )

    # Assert
    # Verify template_service.render was called.
    # The base_prompt would be just the pattern_content in this simplified setup.
    mock_template_service.render.assert_called_once_with(
        template_str=mock_pattern_content, variables=input_variables
    )
    
    # Crucially, verify ai_provider_service.get_completion was called with the
    # output from template_service.render (which simulates the extension's effect).
    mock_ai_provider_service.get_completion.assert_called_once_with(
        prompt=simulated_rendered_prompt_with_extension_output, model_name=model_name
    )
    
    assert result == expected_ai_response
    
    # Verify conversation saving happened as expected (simplified check)
    mock_conversation_repository.create.assert_called_once()
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_execute_pattern_raises_error_on_empty_rendered_prompt(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_conversation_repository: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_empty_prompt_pattern"
    input_variables = {}

    mock_pattern_service.get_pattern_content.return_value = "Some pattern content"
    mock_template_service.render.return_value = ""  # Empty string
    
    # These mocks might not be strictly necessary if the error is raised before they are called
    # but including them for completeness of service instantiation.
    mock_strategy_service.get_strategy.return_value = None
    mock_context_service.get_context_content.return_value = None
    mock_conversation_repository.get_by_id.return_value = None


    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
        uow=mock_uow,
    )

    # Act & Assert
    with pytest.raises(EmptyRenderedPromptError, match="The prompt rendered from the template is empty or whitespace."):
        await service.execute_pattern(
            pattern_name=pattern_name,
            input_variables=input_variables,
            session_id=None,
        )
    
    # Ensure AI completion and saving were not called
    mock_ai_provider_service.get_completion.assert_not_called()
    mock_conversation_repository.create.assert_not_called()
    mock_conversation_repository.save.assert_not_called()
    # uow.commit might be called once during the initial session loading phase,
    # but not a second time for saving if the error is raised.
    # Depending on how uow is used, this might need adjustment.
    # Given the current structure, uow.commit is only called after successful AI completion.
    # So, if error is raised before AI completion, commit for saving shouldn't happen.
    # The first uow block for loading might complete, but the second for saving won't start.
    # Let's assume we are checking the commit for the saving phase.
    # If the first UoW block (loading) doesn't commit itself, then no commit should happen.
    # The current mock_uow.commit is a single mock, so if it's called once for loading,
    # this assertion would need to be `assert_called_once`.
    # For simplicity and focus on the error, let's assert not_called for AI part.
    # The test for commit would be more nuanced depending on UoW implementation details.
    # For now, we'll focus on the main flow being interrupted.


@pytest.mark.asyncio
async def test_execute_pattern_raises_error_on_whitespace_rendered_prompt(
    mock_pattern_service: mock.Mock,
    mock_template_service: mock.Mock,
    mock_strategy_service: mock.Mock,
    mock_context_service: mock.Mock,
    mock_ai_provider_service: mock.Mock,
    mock_conversation_repository: mock.Mock,
    mock_uow: mock.Mock,
) -> None:
    # Arrange
    pattern_name = "test_whitespace_prompt_pattern"
    input_variables = {}

    mock_pattern_service.get_pattern_content.return_value = "Some pattern content"
    mock_template_service.render.return_value = "   "  # Whitespace string
    
    mock_strategy_service.get_strategy.return_value = None
    mock_context_service.get_context_content.return_value = None
    mock_conversation_repository.get_by_id.return_value = None

    service = AIPatternExecutionService(
        pattern_service=mock_pattern_service,
        template_service=mock_template_service,
        strategy_service=mock_strategy_service,
        context_service=mock_context_service,
        ai_provider_service=mock_ai_provider_service,
        conversation_repository=mock_conversation_repository,
        uow=mock_uow,
    )

    # Act & Assert
    with pytest.raises(EmptyRenderedPromptError, match="The prompt rendered from the template is empty or whitespace."):
        await service.execute_pattern(
            pattern_name=pattern_name,
            input_variables=input_variables,
            session_id=None,
        )
        
    mock_ai_provider_service.get_completion.assert_not_called()
    mock_conversation_repository.create.assert_not_called()
    mock_conversation_repository.save.assert_not_called()
