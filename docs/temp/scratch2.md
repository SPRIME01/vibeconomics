# Vibeconomics Agentic Framework - Progress Update & Next Steps (Fabric Integration)

**Important Notes for You When Using These Prompts with Copilot:**

* **Iterate and Verify:** Copilot is a powerful tool, but always review, test, and refine the code it generates. These prompts are a guide.
* **Context is Key:** Provide Copilot with the relevant existing code or file structure when it's working on a specific file. You might need to paste in the content of related files or the overall project structure.
* **File Paths:** I'll use the directory structure we defined. Ensure Copilot creates files in the correct locations.
* **Mocks:** For tests, Copilot will need to generate mocks. Be clear about what needs mocking. `pytest-mock` (using the `mocker` fixture) is a good choice.
* **Strict Typing:** Continuously remind Copilot (if needed) that all Python code must use strict type hints as per PEP 484 and be Mypy compliant.

Here's the series of prompts:

---

## Phase 0: Verification and Foundation Solidification

This phase ensures the work described in `vibe_update.md` is stable and testable.

### Step 0.1: Core Architecture Base Classes

**Prompt 0.1.1 (Test - AggregateRoot):**
"In `backend/tests/domain/test_core_models.py`, write a `pytest` test for a base `AggregateRoot` class.
The `AggregateRoot` should:

1. Initialize with an `id` (e.g., `UUID`).
2. Have a method `add_event(event: DomainEvent)` that stores events in a private list.
3. Have a method `pull_events() -> List[DomainEvent]` that returns all stored events and clears the internal list.
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

1. `AbstractUnitOfWork`: Should define `__aenter__`, `__aexit__`, `commit()`, `rollback()` methods. It should also have a way to register and access repositories (e.g., `repositories: Dict[str, Any]`).
2. `AbstractMessageBus`: Should define a `publish(event: DomainEvent)` method.
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

1. Mock the `mem0.Mem0` client.
2. Instantiate `Mem0Adapter` with the mocked client.
3. Call the `add` method of the adapter with sample data (e.g., `user_id`, `text_content`, `metadata`).
4. Assert that the `mem0.Mem0.add` method was called correctly on the mock client with the expected arguments.
5. Assert that the adapter's `add` method returns the ID from the mocked client's response.
Ensure strict typing and use `mocker` fixture for mocking."

**Prompt 0.3.2 (Test - Mem0Adapter - Search Memory):**
"In `backend/tests/adapters/test_mem0_adapter.py`, write a `pytest` test named `test_mem0_adapter_search_memory_items` for the `Mem0Adapter`.
This test should:

1. Mock the `mem0.Mem0` client.
2. Instantiate `Mem0Adapter` with the mocked client.
3. Mock the return value of `mem0.Mem0.search` to be a list of sample search results.
4. Call the `search` method of the adapter with a sample query (e.g., `user_id`, `search_text`).
5. Assert that the `mem0.Mem0.search` method was called correctly.
6. Assert that the adapter's `search` method returns the expected list of results.
Ensure strict typing."

**Prompt 0.3.3 (Implement/Verify - Mem0Adapter):**
"In `backend/src/app/adapters/mem0_adapter.py`, ensure the `Mem0Adapter` class is implemented.
It should:

1. Initialize with a `mem0.Mem0` client instance.
2. Implement an `add(data: Dict[str, Any]) -> Optional[str]` method that calls `self.client.add(**data)` and returns the `id` from the response.
3. Implement a `search(query: Dict[str, Any]) -> List[Any]` method that calls `self.client.search(**query)` and returns the results.
4. Implement any other necessary methods like `get`, `update`, `delete` if they are part of its contract (define a simple contract if none exists).
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

1. Mock `AbstractMemoryRepository` (which `Mem0Adapter` implements), `AbstractUnitOfWork`, and `AbstractMessageBus`.
2. Test that the handler correctly calls the repository's `add` method.
3. Test that `uow.commit()` is called.
4. Test that `message_bus.publish()` is called with a `MemoryStoredEvent` (define this event in `backend/src/app/domain/memory/events.py`).
Ensure strict typing."

**Prompt 0.4.2 (Test - SearchMemoryQueryHandler):**
"In `backend/tests/service_layer/query_handlers/test_memory_query_handlers.py` (create if not exists), verify/write `pytest` tests for `SearchMemoryQueryHandler`.
The tests should:

1. Mock `AbstractMemoryRepository`.
2. Test that the handler correctly calls the repository's `search` method.
3. Test that it returns the `MemoryQueryResult` (define this DTO in `backend/src/app/domain/memory/models.py`).
Queries typically don't use UoW or publish events. Ensure strict typing."

*(Implementation/Refactor for these handlers will come *after* the AI engine is built, if they need to use patterns. For now, ensure their current direct logic is well-tested).*

---

## Phase 1: Building the Internal Fabric-Inspired Engine

This is where we build the new engine components.

### Step 1.1: PatternService

**Prompt 1.1.1 (Test - PatternService - Load Pattern):**
"In `backend/tests/service_layer/test_pattern_service.py`, write a `pytest` test `test_load_valid_pattern` for `PatternService`.
It should:

1. Mock filesystem operations (e.g., `os.path.exists`, `open`, `read`).
2. Assume patterns are Markdown files in `backend/src/app/patterns/`.
3. Test that `PatternService.get_pattern_content(pattern_name: str)` successfully reads and returns the content of a mocked pattern file (e.g., `backend/src/app/patterns/test_pattern.md`).
4. Test that it raises a `PatternNotFoundError` (custom exception) if the pattern file doesn't exist.
Ensure strict typing."

**Prompt 1.1.2 (Test - PatternService - List Patterns):**
"In `backend/tests/service_layer/test_pattern_service.py`, write a `pytest` test `test_list_available_patterns` for `PatternService`.
It should:

1. Mock `os.listdir` and `os.path.isfile` to simulate a `patterns` directory with a few `.md` files and other file types.
2. Test that `PatternService.list_patterns()` returns a list of only the base names of the `.md` files (without the extension).
Ensure strict typing."

**Prompt 1.1.3 (Implement - PatternService):**
"In `backend/src/app/service_layer/pattern_service.py`, implement `PatternService`.
It should have:

1. A constructor that takes the base path to the patterns directory (e.g., `Path("backend/src/app/patterns/")`).
2. A method `get_pattern_content(pattern_name: str) -> str`.
3. A method `list_patterns() -> List[str]`.
4. Define a custom exception `PatternNotFoundError`.
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

1. Test `TemplateService.render(template_content: str, variables: Dict[str, Any]) -> str`.
2. Use a sample template string like `Hello {{name}}! Today is {{day}}.`
3. Provide variables `{'name': 'World', 'day': 'Monday'}`.
4. Assert the rendered output is `Hello World! Today is Monday.`.
5. Test that it raises a `MissingVariableError` (custom exception) if a variable in the template is not provided in the `variables` dict.
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

1. Mock filesystem operations.
2. Test `StrategyService.get_strategy(strategy_name: str) -> Strategy` (where `Strategy` is a Pydantic model).
3. Assert it correctly loads and parses a mocked strategy JSON file (e.g., `backend/src/app/strategies/test_strategy.json`).
4. Test for `StrategyNotFoundError` (custom exception) if not found or `InvalidStrategyFormatError` if JSON is malformed or missing keys.
Ensure strict typing."

**Prompt 1.3.2 (Test - StrategyService - List Strategies):**
"In `backend/tests/service_layer/test_strategy_service.py`, write `test_list_available_strategies`.

1. Mock `os.listdir` and `os.path.isfile` for the `strategies` directory containing `.json` files.
2. Test `StrategyService.list_strategies()` returns a list of `Strategy` objects (or just names, decide and be consistent).
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

1. `test_get_valid_context`: Mocks filesystem, tests `ContextService.get_context_content(context_name: str) -> str` reads a text file from `backend/src/app/contexts/`. Test for `ContextNotFoundError`.
2. `test_list_available_contexts`: Mocks filesystem, tests `ContextService.list_contexts()` returns names of `.txt` (or other chosen extension) files.
Ensure strict typing."

**Prompt 1.4.2 (Implement - ContextService):**
"In `backend/src/app/service_layer/context_service.py`, implement `ContextService` with `get_context_content` and `list_contexts`. Define `ContextNotFoundError`. Make tests pass. Ensure strict typing."

**Prompt 1.4.3 (Refactor - ContextService):**
"Review `ContextService`. Consider caching. Ensure robust error handling and path management."

### Step 1.5: AIProviderService (with LiteLLM)

**Prompt 1.5.1 (Test - AIProviderService - Basic Completion):**
"In `backend/tests/service_layer/test_ai_provider_service.py`, write `test_get_completion_with_litellm` for `AIProviderService`.

1. Mock `litellm.completion`.
2. Instantiate `AIProviderService`.
3. Call `ai_provider_service.get_completion(prompt: str, model_name: str, **kwargs) -> str`.
4. Assert `litellm.completion` was called with the correct `model`, `messages` (prompt formatted as user message), and any other relevant kwargs.
5. Assert the service returns the content from the mocked LiteLLM response.
Ensure strict typing."

**Prompt 1.5.2 (Test - AIProviderService - Streaming Completion):**
"In `backend/tests/service_layer/test_ai_provider_service.py`, write `test_get_streaming_completion_with_litellm` for `AIProviderService`.

1. Mock `litellm.completion` to return a generator of chunks (like LiteLLM's streaming response).
2. Call `ai_provider_service.get_streaming_completion(prompt: str, model_name: str, **kwargs) -> AsyncGenerator[str, None]`.
3. Iterate over the async generator and assert it yields the content from the mocked chunks.
4. Assert `litellm.completion` was called with `stream=True`.
Ensure strict typing."

**Prompt 1.5.3 (Implement - AIProviderService):**
"In `backend/src/app/service_layer/ai_provider_service.py`, implement `AIProviderService`.
It should have:

1. `async get_completion(...) -> str`.
2. `async get_streaming_completion(...) -> AsyncGenerator[str, None]`.
These methods should use `litellm.completion`.
Make tests pass. Ensure strict typing. Handle LiteLLM exceptions gracefully."

**Prompt 1.5.4 (Refactor - AIProviderService):**
"Review `AIProviderService`.

1. Add configuration for LiteLLM API keys if needed (though LiteLLM often uses environment variables).
2. Consider how DSPy prompts or Outlines model enforcement could be integrated here. For now, focus on LiteLLM. Later, this service could take a DSPy-compiled prompt string, or use Outlines to validate/parse the response from LiteLLM.
3. Standardize error handling for LiteLLM calls."

### Step 1.6: Conversation Aggregate and Repository

**Prompt 1.6.1 (Test - Conversation Aggregate):**
"In `backend/tests/domain/agent/test_agent_models.py`, write tests for the `Conversation` aggregate (in `backend/src/app/domain/agent/models.py`).
It should:

1. Be an `AggregateRoot`.
2. Have a `conversation_id: UUID` (which is its `id`).
3. Store a list of messages (e.g., `List[ChatMessage]`, where `ChatMessage` is a Pydantic model with `role: str` and `content: str`).
4. Have a method `add_message(role: str, content: str)` that appends a `ChatMessage` and potentially raises a `ConversationMessageAddedEvent`.
5. Have a method to get all messages.
Ensure strict typing."

**Prompt 1.6.2 (Implement - Conversation Aggregate):**
"In `backend/src/app/domain/agent/models.py`, implement the `Conversation` aggregate and `ChatMessage` Pydantic model.
In `backend/src/app/domain/agent/events.py`, define `ConversationMessageAddedEvent`.
Make tests pass. Ensure strict typing."

**Prompt 1.6.3 (Test - AbstractConversationRepository):**
"In `backend/tests/service_layer/test_conversation_repository.py`, define tests for an `AbstractConversationRepository` (using `typing.Protocol`).
It should have methods:

1. `async get_by_id(conversation_id: UUID) -> Optional[Conversation]`.
2. `async save(conversation: Conversation) -> None`.
3. `async create(conversation: Conversation) -> None`. (Or `save` handles both create/update).
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

1. Simulate a call to `execute_pattern` with a pattern name, input variables, optional strategy, context, session ID, and model name.
2. Assert `PatternService.get_pattern_content` is called.
3. Assert `ContextService.get_context_content` is called (if context name provided).
4. Assert `StrategyService.get_strategy` is called (if strategy name provided).
5. Assert `TemplateService.render` is called with the combined prompt parts and input variables.
6. Assert `AbstractConversationRepository.get_by_id` is called (if session ID provided) and `save` is called.
7. Assert `AIProviderService.get_completion` (or streaming variant) is called with the final rendered prompt and model name.
8. Assert the method returns the AI's response.
Ensure strict typing."

**Prompt 1.7.2 (Test - AIPatternExecutionService - Session Handling):**
"In `backend/tests/service_layer/test_ai_pattern_execution_service.py`, write tests for session handling:

1. `test_execute_pattern_creates_new_session`: If no `session_id` is provided but session persistence is implied, a new `Conversation` is created and saved.
2. `test_execute_pattern_loads_existing_session`: If `session_id` is provided, `ConversationRepository.get_by_id` is called, messages are appended, and saved.
Ensure strict typing."

**Prompt 1.7.3 (Test - AIPatternExecutionService - Template Extensions - Placeholder):**
*(We'll implement actual extensions later. For now, test the mechanism if `TemplateService` supports it).*
"If `TemplateService` is designed to support `{{extension:name:arg}}` style calls that invoke Python functions:
In `backend/tests/service_layer/test_ai_pattern_execution_service.py`, write a placeholder test `test_execute_pattern_with_template_extension`.
This test would mock `TemplateService.render` to simulate it calling a registered extension and returning its output as part of the rendered prompt. This is more a test of integration design."

**Prompt 1.7.4 (Implement - AIPatternExecutionService):**
"In `backend/src/app/service_layer/ai_pattern_execution_service.py`, implement `AIPatternExecutionService`.
It should:

1. Inject `PatternService`, `TemplateService`, `StrategyService`, `ContextService`, `AIProviderService`, `AbstractConversationRepository`, `AbstractUnitOfWork` via constructor.
2. Implement `async execute_pattern(pattern_name: str, input_variables: Dict[str, Any], ..., output_model: Optional[Type[BaseModel]] = None) -> Any`.
    * Orchestrate calls to the injected services as per the test logic.
    * Handle session loading/creation/saving.
    * Construct the final prompt by combining pattern, context (if any), strategy (if any), and rendered input variables. Prepend strategy prompt, then context, then pattern.
    * Call `AIProviderService`.
    * If `output_model` is provided, attempt to parse the AI response into this Pydantic model (potentially using Outlines via `AIProviderService` in a future step, or basic Pydantic parsing here).
Make tests pass. Ensure strict typing."

**Prompt 1.7.5 (Refactor - AIPatternExecutionService):**
"Review `AIPatternExecutionService`.

1. Ensure clear separation of concerns in prompt assembly.
2. Refine error handling (e.g., what if a pattern renders an empty prompt?).
3. Consider the order of applying strategy, context, and pattern content to the final prompt. (Typically: History -> Strategy -> Context -> Pattern with User Input).
4. How are messages (user, assistant, system) structured for `AIProviderService`? Ensure this is handled correctly, especially with session history."

---

## Phase 2: API Endpoint for Pattern Execution

### Step 2.1: FastAPI Endpoint

**Prompt 2.1.1 (Test - Pattern Execution API Endpoint):**
"In `backend/tests/entrypoints/api/routes/test_agent_commands_api.py` (or a new `test_pattern_executor_api.py`), write `pytest` tests for a FastAPI endpoint `/execute-pattern`.
This endpoint should:

1. Accept `POST` requests with a JSON body (e.g., `pattern_name`, `input_variables`, `session_id`, `model_name`).
2. Mock `AIPatternExecutionService`.
3. Assert that the endpoint correctly calls `AIPatternExecutionService.execute_pattern` with the provided parameters.
4. Assert it returns the response from the service.
5. Test for validation errors (e.g., missing `pattern_name`).
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

1. Mock `Mem0Adapter`.
2. Register a `mem0_add_extension_function` with `TemplateService` that uses the mocked `Mem0Adapter`.
3. Test `TemplateService.render("{{mem0:add:user_id=test_user,text_content=Hello Mem0}}", {})`.
4. Assert `mem0_adapter.add` was called with `{'user_id': 'test_user', 'text_content': 'Hello Mem0'}`.
5. Assert the extension returns the memory ID (or empty string/status).
Ensure strict typing. The extension function should parse its arguments."

**Prompt 3.1.2 (Implement - Mem0 Template Extension - Add):**
"In `backend/src/app/service_layer/template_service.py` (or a new `template_extensions.py`):

1. Modify `TemplateService` to support registering and calling custom extension functions based on a syntax like `{{namespace:operation:key1=val1,key2=val2}}`.
2. Implement `mem0_add_extension_function(mem0_adapter: Mem0Adapter, **kwargs) -> str` that calls `mem0_adapter.add`.
3. Ensure `TemplateService` can be initialized or configured with an instance of `Mem0Adapter` to be passed to the extension.
Make `test_mem0_add_extension` pass. Ensure strict typing."
*(This requires `TemplateService` to be more advanced than simple variable replacement).*

**Prompt 3.1.3 (Refactor - Mem0 Template Extension & TemplateService):**
"Review the template extension mechanism in `TemplateService` and the `mem0_add` extension.

1. Make the extension argument parsing robust.
2. Consider security implications of extensions if they can execute arbitrary code or access any adapter.
3. How are dependencies (like `Mem0Adapter`) injected into extension functions? Ensure this is clean.
4. Implement `mem0:search` extension similarly."

**Prompt 3.1.4 (Refactor - Memory Command/Query Handlers):**
"Review `StoreMemoryCommandHandler` and `SearchMemoryQueryHandler`.
If their logic is simple CRUD and doesn't require AI augmentation (like summarizing before storing), they can continue to use `Mem0Adapter` directly.
If they *do* require AI (e.g., "store this memory and also generate a summary for it"), then:

1. Define a pattern (e.g., `store_and_summarize_memory.md`) that uses the `{{mem0:add:...}}` extension and LLM calls.
2. Refactor the command/query handler to call `AIPatternExecutionService.execute_pattern` with this new pattern, instead of directly calling `Mem0Adapter`.
Write tests for this refactoring."

### Step 3.2: OpenAI-Compatible Endpoint (`/v1/chat/completions`) Refactor

**Prompt 3.2.1 (Test - Chat Command Handler with AI Engine):**
"In `backend/tests/service_layer/command_handlers/test_chat_handlers.py`, refactor/write tests for `ProcessUserChatMessageCommandHandler`.
It should now:

1. Mock `AIPatternExecutionService` and `AbstractUnitOfWork` (for `ConversationRepository`).
2. When handling `ProcessUserChatMessageCommand` (containing user message, session ID, model choice):
    * Assert `AIPatternExecutionService.execute_pattern` is called with:
        * A specific pattern name (e.g., `"conversational_chat"`).
        * Input variables including the user's message.
        * The `session_id` from the command.
        * The `model_name` from the command.
3. Assert the handler returns the response from `execute_pattern`.
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

1. Inject `AIPatternExecutionService`.
2. The handler should call `AIPatternExecutionService.execute_pattern`, passing the user's message as an input variable, the session ID, model choice, and the name of your chat pattern (e.g., `"conversational_chat"`).
3. The `Conversation` aggregate (session history) will be managed internally by `AIPatternExecutionService`.
Make tests pass. Ensure strict typing."

**Prompt 3.2.4 (Refactor - OpenAI-Compatible Endpoint):**
"Review the `/v1/chat/completions` endpoint in `backend/src/app/entrypoints/api/routes/openai_compat.py`.
Ensure it correctly creates and dispatches `ProcessUserChatMessageCommand`.
The response format should align with OpenAI's API (or what LibreChat expects). The result from `AIPatternExecutionService` might need mapping to this format.
Ensure streaming is handled correctly if `AIPatternExecutionService` and `AIProviderService` support it and the request asks for it."

---

## Phase 4 & Beyond: NLWeb, MCP, Other Integrations, E2E Tests

This phase focuses on integrating the remaining external services and frontend components, solidifying the application with Fabric-inspired patterns and advanced workflows, and ensuring the entire framework functions correctly with comprehensive End-to-End tests.

Remember to provide the agent with the **relevant existing code and directory structure** as context for each prompt, especially the `vibeconomics` repository itself, which serves as the base application. Reinforce the requirement for **strict type hints and Mypy compliance**.

#### Step 4.1: NLWeb and MCP Integration

Integrate NLWeb to expose application capabilities via natural language and the Model Context Protocol (MCP), allowing discovery and interaction by agents and tools like ActivePieces. This involves creating entrypoints and service layer logic that might leverage the internal AI engine (AIPatternExecutionService) to interpret natural language requests or execute actions defined as patterns.

* **Prompt 4.1.1 (Test - NLWeb /ask Endpoint):** "In `backend/tests/entrypoints/api/routes/test_nlweb_mcp.py`, write a pytest test `test_nlweb_ask_endpoint`. This test should simulate a natural language query to a `/nlweb/ask` endpoint. It should **mock the AIPatternExecutionService** and assert that the service is called with a specific pattern (e.g., 'nlweb_ask_query') and the user's query as input variables. Ensure strict typing."
* **Prompt 4.1.2 (Implement - NLWeb /ask Endpoint):** "In `backend/src/app/entrypoints/api/routes/nlweb_mcp.py`, implement the FastAPI endpoint `/nlweb/ask`. This endpoint should accept a natural language query, potentially user ID or context. It should **create and dispatch a Command or Query** (e.g., `HandleNLWebAskQuery`) to the service layer. The handler for this command/query will use the **AIPatternExecutionService** with a suitable pattern to process the natural language request. Ensure strict typing. Make tests pass."
* **Prompt 4.1.3 (Test - NLWeb /mcp Endpoint):** "In `backend/tests/entrypoints/api/routes/test_nlweb_mcp.py`, write a pytest test `test_mcp_discovery_endpoint`. This test should call a `/nlweb/mcp` endpoint and verify that it returns a valid MCP manifest describing the application's capabilities (exposed as 'tools'). Ensure the manifest structure is correct. Ensure strict typing."
* **Prompt 4.1.4 (Implement - NLWeb /mcp Endpoint):** "In `backend/src/app/entrypoints/api/routes/nlweb_mcp.py`, implement the FastAPI endpoint `/nlweb/mcp`. This endpoint should generate and return a JSON response conforming to the MCP standard, describing the patterns, commands, or queries your application exposes as agent capabilities. **Ensure strict typing.** Make tests pass."
* **Prompt 4.1.5 (Implement - NLWeb/MCP Service Logic):** "In `backend/src/app/service_layer/nlweb_service.py`, implement the service layer logic for handling NLWeb requests and generating the MCP manifest. This service will be used by the entrypoint handlers. It should **interact with PatternService** to discover available patterns that are marked as exposed via NLWeb/MCP. Ensure strict typing."

#### Step 4.2: Mem0 Integration (Advanced Usage via Internal Engine)

While the basic Mem0 adapter and handlers are set up (Phase 0, 1), prompts are needed to ensure Mem0 is effectively used by the internal AI engine and patterns. Mem0 interactions should be accessible via the AIPatternExecutionService, potentially through template extensions or directly within patterns.

* **Prompt 4.2.1 (Test - Memory Access in Template Extension):** "In `backend/tests/service_layer/test_template_extensions.py`, add a test `test_memory_template_extension`. This test should verify that TemplateService can process a template containing a custom extension like `{{memory:search:user_id:query}}`. **Mock the MemoryService** (which in turn uses the Mem0Adapter) and assert that `MemoryService.search` is called with the correct arguments (user_id, query). Assert that the extension's output is correctly substituted into the template. Ensure strict typing."
* **Prompt 4.2.2 (Implement - Memory Template Extension):** "In `backend/src/app/service_layer/template_extensions.py` (create this file), implement a template extension function for memory access, e.g., `memory_search(user_id: str, query: str) -> str`. This function should **use the MemoryService** to search Mem0 and return the results (formatted as a string for now). Register this extension with your TemplateService. Ensure strict typing. Make tests pass."
* **Prompt 4.2.3 (Refactor - ~~AIPatternExecutionService for Memory):** "Review `backend/src/app/service_layer/ai_pattern_execution_service.py`. Ensure that when a pattern is executed, **session history from the Conversation aggregate is automatically included in the prompt** for the AIProviderService. Also, ensure the service can make the MemoryService available to template extensions or directly to the prompt rendering process if patterns use specific syntax for memory retrieval. Ensure strict typing."~~

#### Step 4.3: ActivePieces Integration (Workflow Automation)

Integrate ActivePieces to orchestrate complex workflows, potentially invoking tasks exposed via MCP from your FastAPI application or other services. ActivePieces workflows can be triggered by your backend, or your patterns can invoke ActivePieces as a tool via template extensions or AIPatternExecutionService logic.

* **Prompt 4.3.1 (Test - ActivePieces Template Extension):** ~~"In `backend/tests/service_layer/test_template_extensions.py`, add a test `test_activepieces_extension`. This test should verify that TemplateService can process a template containing an extension like `{{activepieces:run_workflow:workflow_id:input_data}}`. **Mock the ActivePiecesAdapter** and assert that `ActivePiecesAdapter.run_workflow` is called with the correct arguments. Assert that the extension returns the workflow result. Ensure strict typing."~~
* **Prompt 4.3.2 (Implement - ActivePieces Template Extension and Adapter):** ~~"In `backend/src/app/adapters/activepieces_adapter.py`, implement an adapter for interacting with ActivePieces (e.g., using its API client). Include methods like `run_workflow(workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]`. In `backend/src/app/service_layer/template_extensions.py`, implement an extension function `activepieces_run_workflow` that uses this adapter. Register the extension. Ensure strict typing. Make tests pass."~~
* **Prompt 4.3.3 (Implement - Pattern for ActivePieces Use):** ~~"Create a simple Markdown pattern file in `backend/src/app/patterns/run_workflow.md`. This pattern should demonstrate how to use the `{{activepieces:run_workflow:workflow_id:input_data}}` template extension based on user input variables. For example: 'Okay, I will run workflow {{workflow_id}} with this data: {{input_data | json}}'. Ensure strict typing."~~

#### Step 4.4: Google ADK / `python-a2a` Integration (Agent-to-Agent Communication)

Integrate the `python-a2a` library (or a similar Google ADK implementation) for structured Agent-to-Agent (A2A) communication. This involves defining capabilities, handling incoming A2A messages, and enabling your application's agents/patterns to invoke capabilities on other agents.

* **Prompt 4.4.1 (Test - A2A Capability Definition and Message Models):**
    "In `backend/tests/domain/a2a/test_a2a_models.py` (create this directory and file), write pytest tests for A2A message models and capability definitions using `python-a2a` (or equivalent Pydantic models if `python-a2a` doesn't enforce its own base models for this).
    1. Define a Pydantic model for a sample capability's input (e.g., `SummarizeTextA2ARequest`) and output (e.g., `SummarizeTextA2AResponse`). These models should be structured in a way that's compatible with `python-a2a` message formats.
    2. Test the serialization and deserialization of these models.
    3. Define a Pydantic model or a structured dictionary representing the metadata for this 'SummarizeText' capability (e.g., name, description, input schema, output schema) that can be exposed via MCP or an A2A discovery mechanism.
    Ensure strict typing."

* **Prompt 4.4.2 (Implement - A2A Capability Message Models and Service):**
    "In `backend/src/app/domain/a2a/models.py`, implement the Pydantic models tested in 4.4.1 (e.g., `SummarizeTextA2ARequest`, `SummarizeTextA2AResponse`).
    In `backend/src/app/service_layer/a2a_service.py` (create this file), implement an `A2ACapabilityService`.
    This service should:
    1. Allow registration of capabilities (defined by their metadata, including input/output models).
    2. Provide a method to list or retrieve registered capabilities (this will be used by the MCP endpoint and potentially by an A2A discovery mechanism).
    Ensure strict typing. Make tests pass (you'll need to write tests for `A2ACapabilityService` in `backend/tests/service_layer/test_a2a_service.py`)."

* **Prompt 4.4.3 (Test - Incoming A2A Message Handling):**
    "In `backend/tests/entrypoints/api/routes/test_a2a_api.py` (create this file), write pytest tests for an endpoint that handles incoming A2A messages (e.g., `/a2a/execute/{capability_name}`).
    1. Mock the `AIPatternExecutionService` or the specific service/handler that will execute the underlying logic for the capability (e.g., a summarization service).
    2. Simulate an incoming POST request with an A2A-compliant message body (e.g., a serialized `SummarizeTextA2ARequest`).
    3. Assert that the endpoint correctly deserializes the request, identifies the target capability.
    4. Assert that the appropriate backend service (e.g., `AIPatternExecutionService` with a 'summarize_via_a2a' pattern, or a direct call to a summarization function) is called with the correct parameters extracted from the A2A request.
    5. Assert that the endpoint returns an A2A-compliant response (e.g., a serialized `SummarizeTextA2AResponse`).
    Ensure strict typing."

* **Prompt 4.4.4 (Implement - Incoming A2A Message Endpoint and Handler):**
    "In `backend/src/app/entrypoints/api/routes/a2a_api.py`, implement the FastAPI endpoint (e.g., `/a2a/execute/{capability_name}`) for receiving A2A messages.
    This endpoint should:
    1. Use the `A2ACapabilityService` to look up the capability and its expected input/output models.
    2. Deserialize the incoming A2A request.
    3. Dispatch the request to the appropriate internal service or command handler. This might involve:
        * Mapping the A2A request to a specific `AIPatternExecutionService` pattern.
        * Directly invoking a domain service or command handler.
    4. Serialize and return the result in an A2A-compliant response format.
    Inject necessary dependencies (like `A2ACapabilityService`, `AIPatternExecutionService`).
    Ensure strict typing. Make tests pass."

* **Prompt 4.4.5 (Test - Outgoing A2A Call via Adapter):**
    "In `backend/tests/adapters/test_a2a_client_adapter.py` (create this file), write pytest tests for an `A2AClientAdapter`.
    This adapter will be responsible for making outgoing A2A calls to other agents.
    1. Mock the HTTP client (e.g., `httpx.AsyncClient`) or the `python-a2a` library's call mechanism if it abstracts HTTP.
    2. Test a method like `async execute_remote_capability(agent_url: str, capability_name: str, request_payload: BaseModel) -> BaseModel`.
    3. Assert that the adapter correctly formats the outgoing A2A request (URL, headers, body) according to `python-a2a` specifications.
    4. Assert that it correctly deserializes the A2A response from the mocked external agent.
    5. Test error handling (e.g., network errors, non-2xx responses from the remote agent).
    Ensure strict typing."

* **Prompt 4.4.6 (Implement - A2AClientAdapter):**
    "In `backend/src/app/adapters/a2a_client_adapter.py`, implement the `A2AClientAdapter`.
    It should:
    1. Use an HTTP client (like `httpx.AsyncClient`) or the `python-a2a` library's client functions to send A2A messages.
    2. Implement the `async execute_remote_capability` method.
    3. Handle serialization of the outgoing request and deserialization of the incoming response based on the expected Pydantic models and `python-a2a` conventions.
    Ensure strict typing. Make tests pass."

* **Prompt 4.4.7 (Refactor - AIPatternExecutionService for A2A Invocation):**
    "Review `backend/src/app/service_layer/ai_pattern_execution_service.py`.
    1. Modify it to accept an `A2AClientAdapter` dependency.
    2. Enable patterns or template extensions to invoke outgoing A2A calls. This could be through a new template extension like `{{a2a:invoke:agent_url=http://remote.agent/a2a:capability=summarize:payload={{some_variable}} }}`.
    3. The extension function for `a2a:invoke` would use the `A2AClientAdapter` to make the call.
    Write tests in `backend/tests/service_layer/test_template_extensions.py` for this new `a2a:invoke` extension, mocking the `A2AClientAdapter`.
    Ensure strict typing."

#### Step 4.5: Fabric Pattern Implementation (Potentially using A2A)

Implement specific problem-solving patterns inspired by danielmiessler / fabric as DSPy modules or structured patterns. These patterns might now also leverage A2A to delegate sub-tasks to other specialized agents.

* **Prompt 4.5.1 (Test - Fabric-inspired DSPy Pattern with A2A):**
    "In `backend/tests/service_layer/test_agent_reasoning.py` (or `tests/service_layer/test_fabric_patterns.py`), revise or write a new pytest test, e.g., `test_fabric_collaborative_rag_pattern`.
    This test should instantiate a DSPy module that implements a pattern requiring collaboration.
    1. **Mock the `A2AClientAdapter`**.
    2. The DSPy module, when executed, should make a call through the `A2AClientAdapter` to a mocked external agent for a piece of information or a sub-task.
    3. Mock other dependencies like local retrievers or LLMs as before.
    4. Provide sample input and assert that the DSPy module correctly calls the `A2AClientAdapter` and incorporates its (mocked) response into the final output.
    Ensure strict typing."

* **Prompt 4.5.2 (Implement - Fabric-inspired DSPy Pattern with A2A):**
    "In `backend/src/app/service_layer/agent_reasoning.py` (or `fabric_patterns.py`), implement or refactor a DSPy module (e.g., for collaborative RAG or multi-step reasoning).
    1. This module should accept an `A2AClientAdapter` instance (perhaps via its `forward` method context or constructor if DSPy modules are instantiated per request with dependencies).
    2. Within its logic, it should use the `A2AClientAdapter.execute_remote_capability` method to delegate tasks or fetch information from other (mocked for now) agents.
    Ensure strict typing. Make tests pass."

* **Prompt 4.5.3 (Refactor - AIPatternExecutionService for DSPy Modules with A2A):**
    "Review `backend/src/app/service_layer/ai_pattern_execution_service.py`.
    Ensure that when it executes patterns backed by DSPy modules, it can correctly pass the `A2AClientAdapter` instance to these modules if they require it. This might involve inspecting the DSPy module's needs or having a convention for dependency injection into DSPy modules managed by the service.
    Ensure strict typing."

#### Step 4.6: Advanced Pattern and Workflow Development (with A2A)

Develop more complex, multi-step AI patterns leveraging integrated components, including A2A calls.

* **Prompt 4.6.1 (Implement - Complex Workflow Pattern with A2A):**
    "Create/update a Markdown pattern file in `backend/src/app/patterns/delegated_research_and_summarize.md`.
    This pattern should define a workflow that uses the `{{a2a:invoke:...}}` template extension (implemented in 4.4.7) or direct A2A calls if the pattern execution logic is more programmatic.
    For example:
    1. User provides a complex research topic: `{{input_query}}`
    2. Pattern first calls a specialized 'WebSearchAgent' via A2A: `{{a2a:invoke:agent_url=http://websearch.agent/a2a:capability=perform_search:query={{input_query}} }}` to get raw search results.
    3. Then, it calls a 'DataAnalysisAgent' via A2A with the raw results: `{{a2a:invoke:agent_url=http://dataanalysis.agent/a2a:capability=extract_key_points:data={{output_of_step_2}} }}`.
    4. Finally, the local LLM summarizes the key points: `Summarize these key points: {{output_of_step_3}}`.
    Ensure placeholders for relevant input variables and outputs of intermediate A2A calls.
    Write a unit test for rendering this pattern in `backend/tests/service_layer/test_template_service.py`, mocking the `a2a:invoke` extension to return predictable intermediate results."

* ~**Prompt 4.6.2 (Refactor - AIPatternExecutionService for A2A in Complex Logic):**~
    "Review `backend/src/app/service_layer/ai_pattern_execution_service.py`.
    Ensure its `execute_pattern` method robustly handles patterns that make multiple A2A calls via template extensions.
    Consider how to manage context and pass data between A2A call results and subsequent LLM prompts or further A2A calls within the same pattern execution.
    Error handling for failed A2A calls within a pattern is crucial.
    Ensure strict typing."

#### Step 4.7: CopilotKit Integration (Frontend) - Updated for Storybook

* **Prompt 4.7.1 (Frontend - Implement CopilotKit Component with Storybook):** "In the React frontend (`frontend/src/components/`), integrate CopilotKit. Implement a component like `CopilotSidebar` that can be used on various pages. This component should be configured to communicate with your FastAPI backend's `/execute-pattern` endpoint (or a dedicated `/copilot` endpoint that uses the internal engine). Use `useCopilotReadable` to expose relevant frontend state as context for the AI.

**Additionally, create a comprehensive Storybook story** in `frontend/src/components/CopilotSidebar.stories.tsx` that:

1. Demonstrates the component in different states (loading, error, conversation modes)
2. Uses Storybook's **Controls addon** to make props interactive
3. Uses the **Actions addon** to log CopilotKit events and backend calls
4. Includes **accessibility testing** with the A11y addon
5. Provides **documentation** using JSDoc comments and the Docs addon

Mock the CopilotKit provider and backend responses for the Storybook environment. Ensure strict typing (TypeScript)."

* **Prompt 4.7.2 (Frontend - Implement CopilotKit Actions with Storybook Testing):** "In the frontend, implement examples of custom CopilotKit actions using `useCopilotAction`. Create a component like `CopilotActions` that demonstrates these actions in isolation. These actions should allow the AI sidebar to trigger specific UI updates or backend calls based on user commands (e.g., 'Summarize this page', 'Create a task based on this message').

**Create Storybook stories** in `frontend/src/components/CopilotActions.stories.tsx` that:

1. Show each action type in isolation
2. Use **mock backend responses** to demonstrate different scenarios (success, error, loading states)
3. Include interactive controls to trigger actions manually
4. Document the action parameters and expected behaviors
5. Test with different viewport sizes using the **Viewport addon**

These actions will interact with your FastAPI backend through mocked API calls in Storybook, and real calls in the application. Ensure strict typing (TypeScript)."

* **Prompt 4.7.3 (Frontend - CopilotKit Integration Component with Storybook Documentation):** "Create a higher-level integration component `CopilotIntegration` in `frontend/src/components/` that combines the `CopilotSidebar` and `CopilotActions` components and provides the full CopilotKit experience.

**Create a comprehensive Storybook story** in `frontend/src/components/CopilotIntegration.stories.tsx` that:

1. Shows the complete integration in action
2. Demonstrates different **conversation flows** and action sequences
3. Uses the **Backgrounds addon** to test the component against different page backgrounds
4. Includes **performance testing scenarios** with multiple messages
5. Documents the complete integration setup and configuration options

**Additionally, create a dedicated Storybook page** in `frontend/src/stories/CopilotKit-Setup.stories.mdx` that provides:

1. Setup instructions for CopilotKit in the project
2. Configuration examples for different backend endpoints
3. Best practices for implementing custom actions
4. Troubleshooting guide for common integration issues

Ensure strict typing (TypeScript) and comprehensive documentation."

* **Prompt 4.7.4 (Backend Endpoint for CopilotKit - Enhanced for Storybook Testing):** "In `backend/src/app/entrypoints/api/routes/agent_actions.py` (or a new `copilot_api.py`), implement FastAPI endpoints specifically for CopilotKit actions. These endpoints should receive requests from the frontend, **dispatch appropriate Commands or Queries** to the service layer, which will then use the AIPatternExecutionService with specific patterns designed for these actions.

**Additionally, implement a `/copilot/mock` endpoint** that returns predictable responses for Storybook development and testing. This endpoint should:

1. Accept a `scenario` parameter to return different response types (success, error, streaming, etc.)
2. Include realistic delays to simulate actual AI processing time
3. Return structured responses that match your production endpoint format
4. Support CORS for local Storybook development

Create comprehensive API documentation using FastAPI's automatic OpenAPI generation, ensuring the endpoints are well-documented for both frontend developers and Storybook story authors. Ensure strict typing."

* **Prompt 4.7.5 (Storybook Configuration for CopilotKit Development):** "Update the Storybook configuration in `frontend/.storybook/main.js` and `frontend/.storybook/preview.js` to support CopilotKit development:

1. **Configure MSW (Mock Service Worker)** addon for mocking CopilotKit backend calls
2. **Add custom decorators** for CopilotKit provider setup in stories
3. **Configure environment variables** for different backend endpoints (local, staging, mock)
4. **Add custom controls** for testing different AI model configurations
5. **Set up performance monitoring** addons to measure component render times with CopilotKit

Create `frontend/.storybook/copilot-decorator.tsx` that provides a reusable decorator for wrapping components with the CopilotKit provider and necessary mocks. Document the setup in the existing `frontend/STORYBOOK.md` file with a new section on 'CopilotKit Integration Testing'."

#### Step 4.8: End-to-End (E2E) Tests (including A2A scenarios)

Write comprehensive E2E tests.

* **Prompt 4.8.1 (Implement - E2E Chat Flow Test):** "In `backend/tests/e2e/test_e2e_chat.py`, implement a full E2E test for the chat flow. This test should use `fastapi.testclient.TestClient` to simulate requests coming from the frontend (LibreChat's perspective via the `/v1/chat/completions` endpoint). The test should:
    1. Send an initial message.
    2. Send a follow-up message that requires memory/context from the first message.
    3. Assert that the responses are correct, indicating that the **DSPy reasoning, session handling (Conversation Aggregate), and Mem0 memory retrieval/storage** occurred correctly (verification might involve inspecting logs, mock calls, or a test database if set up).
    Ensure strict typing."

* **Prompt 4.8.2 (Implement - E2E Workflow Execution Test with A2A):**
    "In `backend/tests/e2e/test_e2e_workflows.py`, implement an E2E test that verifies the execution of a complex pattern involving **outgoing A2A calls** (e.g., the `delegated_research_and_summarize.md` pattern).
    1. Use `fastapi.testclient.TestClient` to call the `/execute-pattern` endpoint.
    2. **Mock the external A2A agent endpoints** that your `A2AClientAdapter` would call. The mock should return predefined responses for specific A2A capability requests.
    3. Allow the flow through the internal engine (PatternService, TemplateService, AIPatternExecutionService, A2AClientAdapter) to proceed.
    4. Assert that the mocked external A2A agent endpoints were called correctly by your `A2AClientAdapter`.
    5. Assert that the final response from the pattern execution endpoint incorporates the (mocked) results from the A2A calls and is as expected.
    Ensure strict typing."

* **Prompt 4.8.3 (Implement - E2E Incoming A2A Capability Test):**
    "In `backend/tests/e2e/test_e2e_a2a_handling.py` (create this file), implement an E2E test for an **incoming A2A call** to one of your application's exposed capabilities.
    1. Use `fastapi.testclient.TestClient` to send a request to your `/a2a/execute/{capability_name}` endpoint, simulating an external agent making an A2A call.
    2. The request body should be an A2A-compliant message.
    3. Mock any deep dependencies of the capability's implementation if necessary (e.g., if it calls an LLM via `AIProviderService`, mock that to avoid actual LLM calls).
    4. Assert that your endpoint processes the A2A request correctly and returns a valid A2A-compliant response.
    Ensure strict typing."

* **Prompt 4.8.4 (Implement - E2E NLWeb/MCP Interaction Test):** "In `backend/tests/e2e/test_e2e_nlweb_mcp.py`, implement an E2E test that simulates an agent (like ActivePieces) discovering and interacting with your application via MCP. This test should:
    1. Call the `/nlweb/mcp` endpoint to get the manifest.
    2. Parse the manifest to find a specific tool/capability endpoint (this might now include A2A-exposed capabilities).
    3. Call the discovered endpoint with simulated input data, verifying that it correctly **triggers the underlying command/query handler and utilizes the internal AI engine or A2A handling logic** as appropriate.
    Ensure strict typing."

* **Prompt 4.8.5 (Refactor - Testing Infrastructure):**
    "Review the testing setup (`backend/tests/`).
    1. Ensure `conftest.py` provides useful fixtures for mocking key components (UoW, MessageBus, AIProviderService, MemoryService, ActivePiecesAdapter, **`A2AClientAdapter`**, **mock A2A server/responses for external agents**).
    2. Ensure these fixtures are consistently usable across unit, integration, and E2E tests where appropriate.
    3. Ensure the test structure mirrors the source structure.
    Ensure strict typing for all test files."

This detailed breakdown should provide the necessary steps and specifications for the coding agent to complete the framework implementation using TDD and strict typing, integrating the remaining components and architectural patterns. Remember to review the agent's output carefully after each prompt.
