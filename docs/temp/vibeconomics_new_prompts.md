# Vibeconomics Agentic Framework - Progress Update & Next Steps (Fabric Integration)

**Important Notes for You When Using These Prompts with Copilot:**

*   **Iterate and Verify:** Copilot is a powerful tool, but always review, test, and refine the code it generates. These prompts are a guide.
*   **Context is Key:** Provide Copilot with the relevant existing code or file structure when it's working on a specific file. You might need to paste in the content of related files or the overall project structure.
*   **File Paths:** I'll use the directory structure we defined. Ensure Copilot creates files in the correct locations.
*   **Mocks:** For tests, Copilot will need to generate mocks. Be clear about what needs mocking. `pytest-mock` (using the `mocker` fixture) is a good choice.
*   **Strict Typing:** Continuously remind Copilot (if needed) that all Python code must use strict type hints as per PEP 484 and be Mypy compliant.

Here's the series of prompts:

---

## Phase 0: Verification and Foundation Solidification

This phase ensures the work described in `vibe_update.md` is stable and testable.

### Step 0.1: Core Architecture Base Classes

**Prompt 0.1.1 (Test - AggregateRoot):**
"In `backend/tests/domain/test_core_models.py`, write a `pytest` test for a base `AggregateRoot` class.
The `AggregateRoot` should:
1.  Initialize with an `id` (e.g., `UUID`).
2.  Have a method `add_event(event: DomainEvent)` that stores events in a private list.
3.  Have a method `pull_events() -> List[DomainEvent]` that returns all stored events and clears the internal list.
The `DomainEvent` can be a simple `BaseModel` for now.
Ensure strict typing."

**Prompt 0.1.2 (Implement - AggregateRoot):**
"In `backend/src/app/core/base_aggregate.py`, implement the `AggregateRoot` class and a base `DomainEvent` class (as a Pydantic `BaseModel`) to make the tests in `backend/tests/domain/test_core_models.py` pass.
`AggregateRoot` should inherit from `BaseModel`.
Ensure strict typing."

**Prompt 0.1.3 (Refactor - AggregateRoot):**
"Review the `AggregateRoot` and `DomainEvent` implementations in `backend/src/app/core/base_aggregate.py` and their tests in `backend/tests/domain/test_core_models.py`.
Ensure clarity, adherence to DDD principles for an aggregate root, and robust type hinting.
Make sure `pull_events` truly clears the list after returning."

### Step 0.2: Abstract UoW and MessageBus Interfaces

**Prompt 0.2.1 (Test - Interfaces):**
"In `backend/tests/service_layer/test_abstractions.py`, write `pytest` tests to verify the existence and basic structure of abstract interfaces:
1.  `AbstractUnitOfWork`: Should define `__aenter__`, `__aexit__`, `commit()`, `rollback()` methods. It should also have a way to register and access repositories (e.g., `repositories: Dict[str, Any]`).
2.  `AbstractMessageBus`: Should define a `publish(event: DomainEvent)` method.
Use `typing.Protocol` for these interfaces. Ensure strict typing."

**Prompt 0.2.2 (Implement - Interfaces):**
"In `backend/src/app/service_layer/unit_of_work.py`, define the `AbstractUnitOfWork` interface using `typing.Protocol`.
In `backend/src/app/service_layer/message_bus.py`, define the `AbstractMessageBus` interface using `typing.Protocol`.
These implementations should satisfy the tests in `backend/tests/service_layer/test_abstractions.py`.
Ensure strict typing."

**Prompt 0.2.3 (Refactor - Interfaces):**
"Review the `AbstractUnitOfWork` and `AbstractMessageBus` interfaces. Ensure they are well-defined, use `typing.Protocol` correctly, and clearly specify method signatures including async nature where appropriate (e.g., `commit`, `rollback`, `publish` should likely be async). Update tests if method signatures change."

### Step 0.3: Mem0Adapter - Unblocking and Testing

*(Based on `vibe_update.md`, tests for `Mem0Adapter` were blocked. Let's assume the adapter code itself exists but needs solid tests).*

**Prompt 0.3.1 (Test - Mem0Adapter - Add Memory):**
"In `backend/tests/adapters/test_mem0_adapter.py`, write a `pytest` test named `test_mem0_adapter_add_memory_item` for the `Mem0Adapter` class.
This test should:
1.  Mock the `mem0.Mem0` client.
2.  Instantiate `Mem0Adapter` with the mocked client.
3.  Call the `add` method of the adapter with sample data (e.g., `user_id`, `text_content`, `metadata`).
4.  Assert that the `mem0.Mem0.add` method was called correctly on the mock client with the expected arguments.
5.  Assert that the adapter's `add` method returns the ID from the mocked client's response.
Ensure strict typing and use `mocker` fixture for mocking."

**Prompt 0.3.2 (Test - Mem0Adapter - Search Memory):**
"In `backend/tests/adapters/test_mem0_adapter.py`, write a `pytest` test named `test_mem0_adapter_search_memory_items` for the `Mem0Adapter`.
This test should:
1.  Mock the `mem0.Mem0` client.
2.  Instantiate `Mem0Adapter` with the mocked client.
3.  Mock the return value of `mem0.Mem0.search` to be a list of sample search results.
4.  Call the `search` method of the adapter with a sample query (e.g., `user_id`, `search_text`).
5.  Assert that the `mem0.Mem0.search` method was called correctly.
6.  Assert that the adapter's `search` method returns the expected list of results.
Ensure strict typing."

**Prompt 0.3.3 (Implement/Verify - Mem0Adapter):**
"In `backend/src/app/adapters/mem0_adapter.py`, ensure the `Mem0Adapter` class is implemented.
It should:
1.  Initialize with a `mem0.Mem0` client instance.
2.  Implement an `add(data: Dict[str, Any]) -> Optional[str]` method that calls `self.client.add(**data)` and returns the `id` from the response.
3.  Implement a `search(query: Dict[str, Any]) -> List[Any]` method that calls `self.client.search(**query)` and returns the results.
4.  Implement any other necessary methods like `get`, `update`, `delete` if they are part of its contract (define a simple contract if none exists).
Make the tests in `backend/tests/adapters/test_mem0_adapter.py` pass.
Ensure strict typing. Configure Mypy to ignore missing stubs for the `mem0` library if not already done (e.g., in `mypy.ini` or `pyproject.toml`)."
*(You might need to show Copilot the existing `Mem0Adapter` if it needs refactoring vs. creation).*

**Prompt 0.3.4 (Refactor - Mem0Adapter):**
"Review `Mem0Adapter` and its tests. Ensure methods handle potential errors from the `mem0.Mem0` client gracefully (e.g., connection issues, API errors). Improve data validation for inputs if necessary using Pydantic models for request/response structures within the adapter. Ensure comprehensive test coverage for different scenarios."

### Step 0.4: Existing Command/Query Handlers for Memory System (Test Verification)

*(Based on `vibe_update.md`, `StoreMemoryCommandHandler` and `SearchMemoryQueryHandler` were implemented. We need to ensure their tests are robust before refactoring them later to use the new engine).*

**Prompt 0.4.1 (Test - StoreMemoryCommandHandler):**
"In `backend/tests/service_layer/command_handlers/test_memory_handlers.py` (create if not exists, or use `test_memory_commands.py` if that's the old name), verify/write `pytest` tests for `StoreMemoryCommandHandler`.
The tests should:
1.  Mock `AbstractMemoryRepository` (which `Mem0Adapter` implements), `AbstractUnitOfWork`, and `AbstractMessageBus`.
2.  Test that the handler correctly calls the repository's `add` method.
3.  Test that `uow.commit()` is called.
4.  Test that `message_bus.publish()` is called with a `MemoryStoredEvent` (define this event in `backend/src/app/domain/memory/events.py`).
Ensure strict typing."

**Prompt 0.4.2 (Test - SearchMemoryQueryHandler):**
"In `backend/tests/service_layer/query_handlers/test_memory_query_handlers.py` (create if not exists), verify/write `pytest` tests for `SearchMemoryQueryHandler`.
The tests should:
1.  Mock `AbstractMemoryRepository`.
2.  Test that the handler correctly calls the repository's `search` method.
3.  Test that it returns the `MemoryQueryResult` (define this DTO in `backend/src/app/domain/memory/models.py`).
Queries typically don't use UoW or publish events. Ensure strict typing."

*(Implementation/Refactor for these handlers will come *after* the AI engine is built, if they need to use patterns. For now, ensure their current direct logic is well-tested).*

---

## Phase 1: Building the Internal Fabric-Inspired Engine

This is where we build the new engine components.

### Step 1.1: PatternService

**Prompt 1.1.1 (Test - PatternService - Load Pattern):**
"In `backend/tests/service_layer/test_pattern_service.py`, write a `pytest` test `test_load_valid_pattern` for `PatternService`.
It should:
1.  Mock filesystem operations (e.g., `os.path.exists`, `open`, `read`).
2.  Assume patterns are Markdown files in `backend/src/app/patterns/`.
3.  Test that `PatternService.get_pattern_content(pattern_name: str)` successfully reads and returns the content of a mocked pattern file (e.g., `backend/src/app/patterns/test_pattern.md`).
4.  Test that it raises a `PatternNotFoundError` (custom exception) if the pattern file doesn't exist.
Ensure strict typing."

**Prompt 1.1.2 (Test - PatternService - List Patterns):**
"In `backend/tests/service_layer/test_pattern_service.py`, write a `pytest` test `test_list_available_patterns` for `PatternService`.
It should:
1.  Mock `os.listdir` and `os.path.isfile` to simulate a `patterns` directory with a few `.md` files and other file types.
2.  Test that `PatternService.list_patterns()` returns a list of only the base names of the `.md` files (without the extension).
Ensure strict typing."

**Prompt 1.1.3 (Implement - PatternService):**
"In `backend/src/app/service_layer/pattern_service.py`, implement `PatternService`.
It should have:
1.  A constructor that takes the base path to the patterns directory (e.g., `Path("backend/src/app/patterns/")`).
2.  A method `get_pattern_content(pattern_name: str) -> str`.
3.  A method `list_patterns() -> List[str]`.
4.  Define a custom exception `PatternNotFoundError`.
Make the tests in `backend/tests/service_layer/test_pattern_service.py` pass. Ensure strict typing."

**Prompt 1.1.4 (Refactor - PatternService):**
"Review `PatternService` and its tests.
Consider caching loaded patterns in memory to avoid repeated file reads for frequently used patterns (with a way to clear cache if needed).
Ensure robust error handling for file operations.
Make sure paths are handled correctly regardless of OS. Use `pathlib`."

### Step 1.2: TemplateService (Basic Variables)

**Prompt 1.2.1 (Test - TemplateService - Simple Variable Substitution):**
"In `backend/tests/service_layer/test_template_service.py`, write a `pytest` test `test_render_with_simple_variables` for `TemplateService`.
It should:
1.  Test `TemplateService.render(template_content: str, variables: Dict[str, Any]) -> str`.
2.  Use a sample template string like `Hello {{name}}! Today is {{day}}.`
3.  Provide variables `{'name': 'World', 'day': 'Monday'}`.
4.  Assert the rendered output is `Hello World! Today is Monday.`.
5.  Test that it raises a `MissingVariableError` (custom exception) if a variable in the template is not provided in the `variables` dict.
Ensure strict typing. For now, use simple string replacement for `{{variable}}`."

**Prompt 1.2.2 (Implement - TemplateService - Simple Variables):**
"In `backend/src/app/service_layer/template_service.py`, implement `TemplateService` with the `render` method for simple `{{variable}}` substitution.
Define `MissingVariableError`.
Make `test_render_with_simple_variables` pass.
Ensure strict typing. You can use `re.sub` or string methods for replacement initially."

**Prompt 1.2.3 (Refactor - TemplateService - Simple Variables):**
"Review `TemplateService` for simple variable substitution.
Consider using a more robust templating engine like Jinja2 if complex logic (loops, conditionals in templates) is anticipated later, but for now, ensure the current regex/string replacement is robust for basic `{{variable}}` cases.
Improve error messages for `MissingVariableError` to indicate which variable is missing."

### Step 1.3: StrategyService

**Prompt 1.3.1 (Test - StrategyService - Load Strategy):**
"In `backend/tests/service_layer/test_strategy_service.py`, write a `pytest` test `test_load_valid_strategy` for `StrategyService`.
Strategies are JSON files in `backend/src/app/strategies/` with `{'name': str, 'description': str, 'prompt': str}`.
1.  Mock filesystem operations.
2.  Test `StrategyService.get_strategy(strategy_name: str) -> Strategy` (where `Strategy` is a Pydantic model).
3.  Assert it correctly loads and parses a mocked strategy JSON file (e.g., `backend/src/app/strategies/test_strategy.json`).
4.  Test for `StrategyNotFoundError` (custom exception) if not found or `InvalidStrategyFormatError` if JSON is malformed or missing keys.
Ensure strict typing."

**Prompt 1.3.2 (Test - StrategyService - List Strategies):**
"In `backend/tests/service_layer/test_strategy_service.py`, write `test_list_available_strategies`.
1.  Mock `os.listdir` and `os.path.isfile` for the `strategies` directory containing `.json` files.
2.  Test `StrategyService.list_strategies()` returns a list of `Strategy` objects (or just names, decide and be consistent).
Ensure strict typing."

**Prompt 1.3.3 (Implement - StrategyService):**
"In `backend/src/app/service_layer/strategy_service.py`, implement `StrategyService`.
Define Pydantic model `Strategy(name: str, description: str, prompt: str)`.
Implement `get_strategy` and `list_strategies`.
Define `StrategyNotFoundError` and `InvalidStrategyFormatError`.
Make tests pass. Ensure strict typing."

**Prompt 1.3.4 (Refactor - StrategyService):**
"Review `StrategyService`. Consider caching loaded strategies. Ensure robust error handling and path management. `list_strategies` should ideally return `List[Strategy]` for richer info, or `List[str]` (names) if simplicity is preferred for now."

### Step 1.4: ContextService

**(Similar TDD cycle as `PatternService` but for simple text files in `backend/src/app/contexts/`)**

**Prompt 1.4.1 (Test - ContextService - Load/List):**
"In `backend/tests/service_layer/test_context_service.py`, write tests for `ContextService`:
1.  `test_get_valid_context`: Mocks filesystem, tests `ContextService.get_context_content(context_name: str) -> str` reads a text file from `backend/src/app/contexts/`. Test for `ContextNotFoundError`.
2.  `test_list_available_contexts`: Mocks filesystem, tests `ContextService.list_contexts()` returns names of `.txt` (or other chosen extension) files.
Ensure strict typing."

**Prompt 1.4.2 (Implement - ContextService):**
"In `backend/src/app/service_layer/context_service.py`, implement `ContextService` with `get_context_content` and `list_contexts`. Define `ContextNotFoundError`. Make tests pass. Ensure strict typing."

**Prompt 1.4.3 (Refactor - ContextService):**
"Review `ContextService`. Consider caching. Ensure robust error handling and path management."

### Step 1.5: AIProviderService (with LiteLLM)

**Prompt 1.5.1 (Test - AIProviderService - Basic Completion):**
"In `backend/tests/service_layer/test_ai_provider_service.py`, write `test_get_completion_with_litellm` for `AIProviderService`.
1.  Mock `litellm.completion`.
2.  Instantiate `AIProviderService`.
3.  Call `ai_provider_service.get_completion(prompt: str, model_name: str, **kwargs) -> str`.
4.  Assert `litellm.completion` was called with the correct `model`, `messages` (prompt formatted as user message), and any other relevant kwargs.
5.  Assert the service returns the content from the mocked LiteLLM response.
Ensure strict typing."

**Prompt 1.5.2 (Test - AIProviderService - Streaming Completion):**
"In `backend/tests/service_layer/test_ai_provider_service.py`, write `test_get_streaming_completion_with_litellm` for `AIProviderService`.
1.  Mock `litellm.completion` to return a generator of chunks (like LiteLLM's streaming response).
2.  Call `ai_provider_service.get_streaming_completion(prompt: str, model_name: str, **kwargs) -> AsyncGenerator[str, None]`.
3.  Iterate over the async generator and assert it yields the content from the mocked chunks.
4.  Assert `litellm.completion` was called with `stream=True`.
Ensure strict typing."

**Prompt 1.5.3 (Implement - AIProviderService):**
"In `backend/src/app/service_layer/ai_provider_service.py`, implement `AIProviderService`.
It should have:
1.  `async get_completion(...) -> str`.
2.  `async get_streaming_completion(...) -> AsyncGenerator[str, None]`.
These methods should use `litellm.completion`.
Make tests pass. Ensure strict typing. Handle LiteLLM exceptions gracefully."

**Prompt 1.5.4 (Refactor - AIProviderService):**
"Review `AIProviderService`.
1.  Add configuration for LiteLLM API keys if needed (though LiteLLM often uses environment variables).
2.  Consider how DSPy prompts or Outlines model enforcement could be integrated here. For now, focus on LiteLLM. Later, this service could take a DSPy-compiled prompt string, or use Outlines to validate/parse the response from LiteLLM.
3.  Standardize error handling for LiteLLM calls."

### Step 1.6: Conversation Aggregate and Repository

**Prompt 1.6.1 (Test - Conversation Aggregate):**
"In `backend/tests/domain/agent/test_agent_models.py`, write tests for the `Conversation` aggregate (in `backend/src/app/domain/agent/models.py`).
It should:
1.  Be an `AggregateRoot`.
2.  Have a `conversation_id: UUID` (which is its `id`).
3.  Store a list of messages (e.g., `List[ChatMessage]`, where `ChatMessage` is a Pydantic model with `role: str` and `content: str`).
4.  Have a method `add_message(role: str, content: str)` that appends a `ChatMessage` and potentially raises a `ConversationMessageAddedEvent`.
5.  Have a method to get all messages.
Ensure strict typing."

**Prompt 1.6.2 (Implement - Conversation Aggregate):**
"In `backend/src/app/domain/agent/models.py`, implement the `Conversation` aggregate and `ChatMessage` Pydantic model.
In `backend/src/app/domain/agent/events.py`, define `ConversationMessageAddedEvent`.
Make tests pass. Ensure strict typing."

**Prompt 1.6.3 (Test - AbstractConversationRepository):**
"In `backend/tests/service_layer/test_conversation_repository.py`, define tests for an `AbstractConversationRepository` (using `typing.Protocol`).
It should have methods:
1.  `async get_by_id(conversation_id: UUID) -> Optional[Conversation]`.
2.  `async save(conversation: Conversation) -> None`.
3.  `async create(conversation: Conversation) -> None`. (Or `save` handles both create/update).
Ensure strict typing."

**Prompt 1.6.4 (Implement - AbstractConversationRepository Interface):**
"In `backend/src/app/domain/agent/ports.py` (create this file for repository interfaces, a common DDD practice) or `backend/src/app/service_layer/ports.py`, define the `AbstractConversationRepository` interface using `typing.Protocol`. Make tests pass."

**Prompt 1.6.5 (Implement - InMemoryConversationRepository - for testing):**
"In `backend/tests/adapters/test_conversation_repository_inmemory.py`, write tests for an `InMemoryConversationRepository` that implements `AbstractConversationRepository`.
In `backend/src/app/adapters/conversation_repository_inmemory.py`, implement `InMemoryConversationRepository`. This will be useful for E2E tests later. Make tests pass."

**Prompt 1.6.6 (Refactor - Conversation):**
"Review `Conversation` aggregate, its events, and repository interface. Ensure it captures necessary session state. Consider if `last_updated_at` or other metadata is needed on the `Conversation`."

### Step 1.7: AIPatternExecutionService (The Orchestrator)

This is the most complex service. Break down its tests.

**Prompt 1.7.1 (Test - AIPatternExecutionService - Basic Execution Flow):**
"In `backend/tests/service_layer/test_ai_pattern_execution_service.py`, write `test_execute_pattern_happy_path` for `AIPatternExecutionService`.
Mock: `PatternService`, `TemplateService`, `StrategyService`, `ContextService`, `AIProviderService`, `AbstractConversationRepository`, `AbstractUnitOfWork`.
The test should:
1.  Simulate a call to `execute_pattern` with a pattern name, input variables, optional strategy, context, session ID, and model name.
2.  Assert `PatternService.get_pattern_content` is called.
3.  Assert `ContextService.get_context_content` is called (if context name provided).
4.  Assert `StrategyService.get_strategy` is called (if strategy name provided).
5.  Assert `TemplateService.render` is called with the combined prompt parts and input variables.
6.  Assert `AbstractConversationRepository.get_by_id` is called (if session ID provided) and `save` is called.
7.  Assert `AIProviderService.get_completion` (or streaming variant) is called with the final rendered prompt and model name.
8.  Assert the method returns the AI's response.
Ensure strict typing."

**Prompt 1.7.2 (Test - AIPatternExecutionService - Session Handling):**
"In `backend/tests/service_layer/test_ai_pattern_execution_service.py`, write tests for session handling:
1.  `test_execute_pattern_creates_new_session`: If no `session_id` is provided but session persistence is implied, a new `Conversation` is created and saved.
2.  `test_execute_pattern_loads_existing_session`: If `session_id` is provided, `ConversationRepository.get_by_id` is called, messages are appended, and saved.
Ensure strict typing."

**Prompt 1.7.3 (Test - AIPatternExecutionService - Template Extensions - Placeholder):**
*(We'll implement actual extensions later. For now, test the mechanism if `TemplateService` supports it).*
"If `TemplateService` is designed to support `{{extension:name:arg}}` style calls that invoke Python functions:
In `backend/tests/service_layer/test_ai_pattern_execution_service.py`, write a placeholder test `test_execute_pattern_with_template_extension`.
This test would mock `TemplateService.render` to simulate it calling a registered extension and returning its output as part of the rendered prompt. This is more a test of integration design."

**Prompt 1.7.4 (Implement - AIPatternExecutionService):**
"In `backend/src/app/service_layer/ai_pattern_execution_service.py`, implement `AIPatternExecutionService`.
It should:
1.  Inject `PatternService`, `TemplateService`, `StrategyService`, `ContextService`, `AIProviderService`, `AbstractConversationRepository`, `AbstractUnitOfWork` via constructor.
2.  Implement `async execute_pattern(pattern_name: str, input_variables: Dict[str, Any], ..., output_model: Optional[Type[BaseModel]] = None) -> Any`.
    *   Orchestrate calls to the injected services as per the test logic.
    *   Handle session loading/creation/saving.
    *   Construct the final prompt by combining pattern, context (if any), strategy (if any), and rendered input variables. Prepend strategy prompt, then context, then pattern.
    *   Call `AIProviderService`.
    *   If `output_model` is provided, attempt to parse the AI response into this Pydantic model (potentially using Outlines via `AIProviderService` in a future step, or basic Pydantic parsing here).
Make tests pass. Ensure strict typing."

**Prompt 1.7.5 (Refactor - AIPatternExecutionService):**
"Review `AIPatternExecutionService`.
1.  Ensure clear separation of concerns in prompt assembly.
2.  Refine error handling (e.g., what if a pattern renders an empty prompt?).
3.  Consider the order of applying strategy, context, and pattern content to the final prompt. (Typically: History -> Strategy -> Context -> Pattern with User Input).
4.  How are messages (user, assistant, system) structured for `AIProviderService`? Ensure this is handled correctly, especially with session history."

---

## Phase 2: API Endpoint for Pattern Execution

### Step 2.1: FastAPI Endpoint

**Prompt 2.1.1 (Test - Pattern Execution API Endpoint):**
"In `backend/tests/entrypoints/api/routes/test_agent_commands_api.py` (or a new `test_pattern_executor_api.py`), write `pytest` tests for a FastAPI endpoint `/execute-pattern`.
This endpoint should:
1.  Accept `POST` requests with a JSON body (e.g., `pattern_name`, `input_variables`, `session_id`, `model_name`).
2.  Mock `AIPatternExecutionService`.
3.  Assert that the endpoint correctly calls `AIPatternExecutionService.execute_pattern` with the provided parameters.
4.  Assert it returns the response from the service.
5.  Test for validation errors (e.g., missing `pattern_name`).
Ensure strict typing."

**Prompt 2.1.2 (Implement - Pattern Execution API Endpoint):**
"In `backend/src/app/entrypoints/api/routes/agent_commands_api.py` (or a new `pattern_executor_api.py`), implement the `/execute-pattern` FastAPI endpoint.
Use Pydantic models for request and response bodies.
Inject and use `AIPatternExecutionService`.
Make tests pass. Ensure strict typing."

**Prompt 2.1.3 (Refactor - Pattern Execution API Endpoint):**
"Review the `/execute-pattern` endpoint. Ensure robust error handling (e.g., what if `AIPatternExecutionService` raises an exception?). Standardize API response format. Consider authentication/authorization if applicable."

---

## Phase 3: Refactor/Integrate Existing Systems with the New Engine

### Step 3.1: Mem0Adapter Integration via Template Extensions

**Prompt 3.1.1 (Test - Mem0 Template Extension - Add):**
"In `backend/tests/service_layer/test_template_service_extensions.py`, write `test_mem0_add_extension`.
Assume `TemplateService` can register and call extensions like `{{mem0:add:user_id=test,text=hello}}`.
1.  Mock `Mem0Adapter`.
2.  Register a `mem0_add_extension_function` with `TemplateService` that uses the mocked `Mem0Adapter`.
3.  Test `TemplateService.render("{{mem0:add:user_id=test_user,text_content=Hello Mem0}}", {})`.
4.  Assert `mem0_adapter.add` was called with `{'user_id': 'test_user', 'text_content': 'Hello Mem0'}`.
5.  Assert the extension returns the memory ID (or empty string/status).
Ensure strict typing. The extension function should parse its arguments."

**Prompt 3.1.2 (Implement - Mem0 Template Extension - Add):**
"In `backend/src/app/service_layer/template_service.py` (or a new `template_extensions.py`):
1.  Modify `TemplateService` to support registering and calling custom extension functions based on a syntax like `{{namespace:operation:key1=val1,key2=val2}}`.
2.  Implement `mem0_add_extension_function(mem0_adapter: Mem0Adapter, **kwargs) -> str` that calls `mem0_adapter.add`.
3.  Ensure `TemplateService` can be initialized or configured with an instance of `Mem0Adapter` to be passed to the extension.
Make `test_mem0_add_extension` pass. Ensure strict typing."
*(This requires `TemplateService` to be more advanced than simple variable replacement).*

**Prompt 3.1.3 (Refactor - Mem0 Template Extension & TemplateService):**
"Review the template extension mechanism in `TemplateService` and the `mem0_add` extension.
1.  Make the extension argument parsing robust.
2.  Consider security implications of extensions if they can execute arbitrary code or access any adapter.
3.  How are dependencies (like `Mem0Adapter`) injected into extension functions? Ensure this is clean.
4.  Implement `mem0:search` extension similarly."

**Prompt 3.1.4 (Refactor - Memory Command/Query Handlers):**
"Review `StoreMemoryCommandHandler` and `SearchMemoryQueryHandler`.
If their logic is simple CRUD and doesn't require AI augmentation (like summarizing before storing), they can continue to use `Mem0Adapter` directly.
If they *do* require AI (e.g., "store this memory and also generate a summary for it"), then:
1.  Define a pattern (e.g., `store_and_summarize_memory.md`) that uses the `{{mem0:add:...}}` extension and LLM calls.
2.  Refactor the command/query handler to call `AIPatternExecutionService.execute_pattern` with this new pattern, instead of directly calling `Mem0Adapter`.
Write tests for this refactoring."

### Step 3.2: OpenAI-Compatible Endpoint (`/v1/chat/completions`) Refactor

**Prompt 3.2.1 (Test - Chat Command Handler with AI Engine):**
"In `backend/tests/service_layer/command_handlers/test_chat_handlers.py`, refactor/write tests for `ProcessUserChatMessageCommandHandler`.
It should now:
1.  Mock `AIPatternExecutionService` and `AbstractUnitOfWork` (for `ConversationRepository`).
2.  When handling `ProcessUserChatMessageCommand` (containing user message, session ID, model choice):
    *   Assert `AIPatternExecutionService.execute_pattern` is called with:
        *   A specific pattern name (e.g., `"conversational_chat"`).
        *   Input variables including the user's message.
        *   The `session_id` from the command.
        *   The `model_name` from the command.
3.  Assert the handler returns the response from `execute_pattern`.
Ensure strict typing."

**Prompt 3.2.2 (Implement - Chat Pattern):**
"In `backend/src/app/patterns/conversational_chat.md`, create a simple pattern for chat.
It should at least include `{{input}}` (for the current user message).
It might also include placeholders for system prompts or personality if desired later.
Example:
```markdown
You are a helpful AI assistant.

User: {{input}}
Assistant:
```
"

**Prompt 3.2.3 (Refactor - Chat Command Handler):**
"In `backend/src/app/service_layer/command_handlers/chat_handlers.py`, refactor `ProcessUserChatMessageCommandHandler`.
1.  Inject `AIPatternExecutionService`.
2.  The handler should call `AIPatternExecutionService.execute_pattern`, passing the user's message as an input variable, the session ID, model choice, and the name of your chat pattern (e.g., `"conversational_chat"`).
3.  The `Conversation` aggregate (session history) will be managed internally by `AIPatternExecutionService`.
Make tests pass. Ensure strict typing."

**Prompt 3.2.4 (Refactor - OpenAI-Compatible Endpoint):**
"Review the `/v1/chat/completions` endpoint in `backend/src/app/entrypoints/api/routes/openai_compat.py`.
Ensure it correctly creates and dispatches `ProcessUserChatMessageCommand`.
The response format should align with OpenAI's API (or what LibreChat expects). The result from `AIPatternExecutionService` might need mapping to this format.
Ensure streaming is handled correctly if `AIPatternExecutionService` and `AIProviderService` support it and the request asks for it."

---

## Phase 4 & Beyond: NLWeb, MCP, Other Integrations, E2E Tests

This follows the same TDD pattern:
1.  **Define Patterns:** For NLWeb actions, MCP tool executions, etc. These patterns might use template extensions to call respective adapters.
2.  **Test Command/Query Handlers:** Handlers should call `AIPatternExecutionService` with these new patterns.
3.  **Implement Handlers.**
4.  **Test and Implement API Entrypoints** that dispatch to these handlers.
5.  **E2E Tests:** Write tests in `backend/tests/e2e/test_e2e_pattern_workflows.py` that make API calls and verify the entire flow, including pattern execution, AI response, and data persistence (e.g., conversation history).

**Example Prompt for an NLWeb action:**

**Prompt (Test - NLWeb Ask Pattern Handler):**
"In `backend/tests/service_layer/query_handlers/test_nlweb_query_handlers.py`, write a test for `HandleNLWebAskQueryHandler`.
It should mock `AIPatternExecutionService` and assert it's called with an `"nlweb_ask"` pattern and the query parameters."

---

This detailed, phased set of prompts should guide Copilot effectively. Remember to provide context and review its output at each step. Good luck!


### References

1. **A Comprehensive Guide to Vibe Coding Tools | by Madhukar Kumar | Mar, 2025 | Medium**. [https://madhukarkumar.medium.com](https://madhukarkumar.medium.com/a-comprehensive-guide-to-vibe-coding-tools-2bd35e2d7b4f)
2. **A Practical Roadmap for Adopting Vibe Coding - The New Stack**. [https://thenewstack.io](https://thenewstack.io/a-practical-roadmap-for-vibe-coding-adoption/)
3. **Vibe coding: Your roadmap to becoming an AI developer - The GitHub Blog**. [https://github.blog](https://github.blog/ai-and-ml/vibe-coding-your-roadmap-to-becoming-an-ai-developer/)
4. **Product Roadmap Guide: What is it & How to Create One | Atlassian**. [https://www.atlassian.com](https://www.atlassian.com/agile/product-management/product-roadmaps)
5. **Vibe coding, some thoughts and predictions - by Andrew Chen**. [https://andrewchen.substack.com](https://andrewchen.substack.com/p/predictionsthoughts-on-vibe-coding)
6. **vibe-coding/README.md at main · EnzeD/vibe-coding**. [https://github.com](https://github.com/EnzeD/vibe-coding/blob/main/README.md)
7. **A Structured Workflow for "Vibe Coding" Full-Stack Apps - DEV Community**. [https://dev.to](https://dev.to/wasp/a-structured-workflow-for-vibe-coding-full-stack-apps-352l)
8. **Vibe Code a Retro Game in 3 Prompts - by Bilgin Ibryam**. [https://generativeprogrammer.com](https://generativeprogrammer.com/p/vibe-code-a-retro-game-in-3-prompts)
9. **What I Learned from Vibe Coding - DEV Community**. [https://dev.to](https://dev.to/erikch/what-i-learned-vibe-coding-30em)
10. **Everything You Want to Know About Product Roadmaps - | Vibe**. [https://vibe.us](https://vibe.us/blog/product-roadmaps/)
