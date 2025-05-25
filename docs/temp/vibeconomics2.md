
## Project Objective

Transform the `vibeconomics` repository into a comprehensive Agentic Application Framework. This involves integrating advanced AI capabilities using Test-Driven Development (TDD), ensuring all Python code adheres to strict typing, and **establishing a sophisticated backend architecture based on Hexagonal principles, CQRS, Domain-Driven Design (DDD) Aggregates, a Unit of Work (UoW) pattern, a Message Bus for domain events, and Dependency Injection (DI). Crucially, this framework will feature an internal, Fabric-inspired orchestration engine for AI-driven task execution, leveraging LiteLLM for broad AI provider access, and utilizing DSPy and Outlines for advanced prompt engineering and structured output control.**

## Development Approach: Test-Driven Development & Strict Typing

For every component, feature, command, query, event handler, and internal engine service integration, you **must** follow this TDD workflow:

1. **Write Tests First:** Create comprehensive tests using `pytest`. Define expected behavior, interfaces, contracts, emitted domain events, and interactions with the internal orchestration engine. All test code and production code must use strict Python type hints.
2. **Implement Minimal Code:** Write the simplest possible production code (with strict type hints) to make the tests pass. This includes defining Aggregates, Commands, Queries, Events, their respective handlers, and the services for the internal engine.
3. **Refactor:** Improve the code's structure and clarity, ensuring adherence to architectural patterns and that all tests continue to pass.
4. **Document:** Add docstrings (with type information) to all public interfaces in both test and production code, including pattern definitions and engine service contracts.

All Python code generated **must** include comprehensive type hints as per PEP 484.

## Repository Structure Context & Architectural Patterns

The `vibeconomics` backend (`backend/src/app/`) aims for a Hexagonal Architecture. You will enhance this by explicitly implementing the following patterns, with the internal Fabric-inspired engine playing a key role in orchestrating AI capabilities:

### Hexagonal Architecture (Ports and Adapters)

-   **`domain/`**: Core business logic, **Aggregates**, Value Objects, and **Domain Events**. This is the heart of the application and must have no dependencies on infrastructure.
    -   `chat/`: Domain models and events specific to chat functionalities.
    -   `memory/`: Domain models (e.g., `MemoryItem`) and events for the memory system.
    -   `agent/`: Domain models (e.g., `Conversation` Aggregate for session history) and events related to agent state and interactions.
-   **`service_layer/`**: Orchestrates use cases and houses the internal AI orchestration engine. This layer will contain:
    -   **Command Handlers:** (e.g., in `command_handlers/chat_handlers.py`, `command_handlers/memory_handlers.py`) Process incoming commands, interact with Aggregates (via Repositories and UoW), and may publish Domain Events. They will delegate complex AI tasks to the `AIPatternExecutionService`.
    -   **Query Handlers:** (e.g., in `query_handlers/memory_query_handlers.py`) Process incoming queries to retrieve data (Read Models). May use the `AIPatternExecutionService` for AI-assisted data interpretation if needed.
    -   **Event Handlers:** (e.g., in `event_handlers/chat_event_handlers.py`) Subscribe to Domain Events from the Message Bus and trigger subsequent actions, potentially including invoking the `AIPatternExecutionService`.
    -   **Internal Fabric-Inspired Engine Services:**
        -   **`PatternService` (`pattern_service.py`)**: Manages loading and retrieval of pattern definitions.
        -   **`TemplateService` (`template_service.py`)**: Processes patterns with dynamic data (variables, template extensions).
        -   **`StrategyService` (`strategy_service.py`)**: Manages loading and application of "thinking style" prompts.
        -   **`ContextService` (`context_service.py`)**: Manages reusable informational snippets for prompts.
        -   **`AIProviderService` (`ai_provider_service.py`)**: Leverages **LiteLLM** for unified access to diverse LLM providers. Can utilize DSPy (potentially via utilities in `llm_services.py`) for prompt construction/optimization before sending requests via LiteLLM, and Outlines for structured output parsing after receiving responses.
        -   **`AIPatternExecutionService` (`ai_pattern_execution_service.py`)**: The central orchestrator for the internal engine. Uses all other engine services to execute AI tasks defined by patterns, manage session history (via `ConversationRepository`), and return results.
    -   `llm_services.py`: May contain lower-level DSPy/Outlines utilities or specific LLM interaction logic supporting `AIProviderService` or template extensions.
    -   `workflow_services.py`: For any high-level, non-pattern-based orchestrations (though preference is for pattern-based execution via `AIPatternExecutionService`).
-   **`adapters/`**: Infrastructure concerns. This includes:
    -   Repositories: Provide an abstraction for persisting and retrieving **Aggregates** (e.g., `MemoryRepository`, `ConversationRepository`). Concrete implementations like `mem0_adapter.py` (acting as a repository for memory), `conversation_repository_sqlmodel.py`.
    -   Unit of Work (UoW): Concrete implementation (e.g., `uow_sqlmodel.py`).
    -   Message Bus: Concrete implementation (e.g., `message_bus_redis.py`).
    -   Clients for external services (ActivePieces, NLWeb if external). These tools can be invoked as "template extensions" or orchestrated by patterns.
-   **`entrypoints/`**: API routes (FastAPI in `api/main.py` with routes in `api/routes/`) and other invocation methods. These will primarily dispatch **Commands** or **Queries**, or directly invoke the `AIPatternExecutionService`.
-   **`core/`**: Shared configuration (`config.py`), base classes (`base_aggregate.py`, `base_event.py`), and core utilities.
-   **`patterns/`**: Definitions of AI task instructions (e.g., Markdown files like `chat.md`).
-   **`strategies/`**: Definitions of "thinking style" prompts (e.g., JSON/Markdown files like `chain_of_thought.json`).
-   **`contexts/`**: Reusable informational snippets for prompts (e.g., text files like `project_guidelines.txt`).

### Additional Patterns

-   **CQRS (Command Query Responsibility Segregation):** Commands in `service_layer/commands/`, Queries in `service_layer/queries/`.
-   **DDD Aggregates:** Defined in `domain/<context>/models.py`.
-   **Unit of Work (UoW):** Interface in `service_layer/unit_of_work.py`, implementation in `adapters/`.
-   **Message Bus:** Interface in `service_layer/message_bus.py`, implementation in `adapters/`.
-   **Dependency Injection (DI):** FastAPI's DI used in `entrypoints/api/dependencies.py` and throughout.
-   **Internal Pattern-Based Orchestration:** Via `AIPatternExecutionService`.

You may need to create new directories (like `patterns/`, `strategies/`, `contexts/`) and files for the internal engine services.

## Core Components and Initial Test Specifications (Strict Typing)

### 1. LibreChat Integration (Entrypoint, using internal engine for chat logic)

This involves the `/v1/chat/completions` endpoint. The handler for this endpoint will likely dispatch a command (e.g., `ProcessUserChatMessageCommand`). The command handler will then use the `AIPatternExecutionService` with a specific "chat" pattern to manage the conversation flow, leveraging session history and the `AIProviderService` (LiteLLM-backed) for LLM interaction.

**Test Specifications:**

```python
# backend/tests/entrypoints/api/routes/test_openai_compat.py
from fastapi.testclient import TestClient
from typing import List, Dict, Any, Generator
import uuid

def test_chat_completion_endpoint_uses_ai_pattern_execution_service(
    client: TestClient,
    mock_ai_pattern_execution_service: Any # Mock the central engine orchestrator
) -> None:
    """Test that the /v1/chat/completions endpoint correctly uses the AIPatternExecutionService."""
    request_id: str = str(uuid.uuid4())
    user_id: str = "test_user_engine"
    request_payload: Dict[str, Any] = {
        "model": "litellm-model/gpt-4", # Model handled by LiteLLM via AIProviderService
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
        "user": user_id,
        "request_id": request_id
    }
    # Mock the execute_pattern method of the service
    mock_ai_pattern_execution_service.execute_pattern.return_value = {
        "response": "Paris is the capital of France.",
        "session_id": "some_session_id"
    }

    response = client.post("/v1/chat/completions", json=request_payload)
    assert response.status_code == 200
    response_data: Dict[str, Any] = response.json()
    assert "choices" in response_data # Or align with actual response structure
    # Verify mock_ai_pattern_execution_service.execute_pattern was called with expected args
    # (e.g., pattern_name="chat_conversation", input_data=..., session_id=...)

# backend/tests/service_layer/command_handlers/test_chat_commands.py
from typing import Dict, Any

def test_process_user_chat_message_command_handler_uses_ai_pattern_service(
    mock_uow: Any, # For Conversation aggregate persistence
    mock_message_bus: Any,
    mock_ai_pattern_execution_service: Any
) -> None:
    """Test the command handler for processing user chat messages via the internal engine."""
    # Test implementation here:
    # 1. Create a ProcessUserChatMessageCommand.
    # 2. Instantiate the handler with the mock AIPatternExecutionService.
    # 3. Call the handler.
    # 4. Assert that mock_ai_pattern_execution_service.execute_pattern was called
    #    with appropriate parameters (e.g., chat pattern, user message, session details).
    # 5. Assert that a Conversation aggregate might be saved via UoW.
    pass
```

# backend/tests/service_layer/command_handlers/test_chat_handlers.py
# ... (test ProcessUserChatMessageCommand handler using mock_ai_pattern_execution_service) ...

**Implementation Notes (LibreChat Configuration):** (Largely unchanged, `baseURL` points to your FastAPI app)

```yaml
# Expected librechat.yaml configuration:
endpoints:
  custom:
    - name: "VibeconomicsEngine"
      apiKey: ${INTERNAL_API_KEY} # Or a general API key for your backend
      baseURL: "http://host.docker.internal:8000/v1" # Your FastAPI app
      models:
        default: ["litellm-model/gpt-4", "litellm-model/claude-3-opus"] # Models LiteLLM can access
      fetch: false
      titleConvo: true
      summarize: false
      forcePrompt: false
      dropParams: ["stop", "user", "frequency_penalty", "presence_penalty"]
      modelDisplayLabel: "Vibeconomics Engine"
```

### 2. Internal Fabric-Inspired Engine (Core Orchestration & Reasoning Services)

This involves building the suite of services: `PatternService`, `TemplateService`, `StrategyService`, `ContextService`, `AIProviderService` (using LiteLLM, DSPy, Outlines), and `AIPatternExecutionService`.

- **Pattern Execution:** The `AIPatternExecutionService` will orchestrate loading patterns, applying strategies/contexts, processing templates, managing session history (via a `ConversationRepository`), and using the `AIProviderService` for LLM calls.
- **`AIProviderService`:** This service will use **LiteLLM** to make calls to various LLM providers. It can use **DSPy** to construct/optimize prompts before sending them via LiteLLM, and **Outlines** to parse/validate structured outputs received from LiteLLM.
- **Template Extensions:** The `TemplateService` will support custom Python functions (template extensions) for dynamic data or tool interactions within patterns.

**Test Specifications:**

```python
# backend/tests/service_layer/test_ai_pattern_execution_service.py
from typing import Any, Dict, List
from pydantic import BaseModel

class SampleStructuredOutput(BaseModel):
    answer: str
    confidence: float

def test_ai_pattern_execution_service_executes_pattern_with_structured_output(
    ai_pattern_execution_service: Any, # Concrete instance or well-configured mock
    mock_ai_provider_service: Any,
    mock_pattern_service: Any,
    mock_template_service: Any,
    mock_conversation_repository: Any
) -> None:
    """Test AIPatternExecutionService executes a pattern that uses LiteLLM (via AIProviderService)
       and aims for structured output (potentially validated by Outlines within AIProviderService)."""
    pattern_name: str = "get_answer_structured"
    input_data: Dict[str, Any] = {"question": "What is 2 + 2?"}

    # Mock services:
    # mock_pattern_service.get_pattern.return_value = "Pattern content with {{input}}"
    # mock_template_service.render.return_value = "Processed prompt"
    # mock_ai_provider_service.get_completion.return_value = {"answer": "4", "confidence": 0.99} # Simulating structured output
    # mock_conversation_repository for session handling

    response: SampleStructuredOutput = ai_pattern_execution_service.execute_pattern(
        pattern_name=pattern_name,
        input_variables=input_data,
        output_model=SampleStructuredOutput # Hint for expected output structure
    )
    assert isinstance(response, SampleStructuredOutput)
    assert response.answer == "4"
    assert isinstance(response.confidence, float)
    # mock_ai_provider_service.get_completion.assert_called_once()

# backend/tests/service_layer/test_ai_provider_service.py
def test_ai_provider_service_uses_litellm(
    ai_provider_service: Any, # Concrete instance
    mock_litellm_completion: Any # Mock litellm.completion
) -> None:
    """Test AIProviderService correctly calls LiteLLM."""
    prompt: str = "Test prompt"
    model_name: str = "gpt-3.5-turbo"
    mock_litellm_completion.return_value = {"choices": [{"message": {"content": "Test response"}}]}

    response: str = ai_provider_service.get_completion(prompt, model_name)
    assert response == "Test response"
    # mock_litellm_completion.assert_called_once_with(model=model_name, messages=[{"role": "user", "content": prompt}])

# backend/tests/service_layer/test_template_service.py
def test_template_service_renders_with_extension(
    template_service: Any,
    mock_custom_extension_function: Any
) -> None:
    """Test TemplateService can render a template using a custom extension."""
    # template_service.register_extension("custom_tool", mock_custom_extension_function)
    # mock_custom_extension_function.return_value = "tool_output"
    # template_content = "Data: {{custom_tool:do_something:input_val}}"
    # rendered_content = template_service.render(template_content, {})
    # assert rendered_content == "Data: tool_output"
    pass
```

### 3. Mem0 Memory System Integration (Adapter, used by patterns for memory operations a handlers like `memory_handlers.py` and `memory_query_handlers.py`)

Memory writes and reads will be orchestrated by patterns executed via `AIPatternExecutionService`. Patterns might use a `{{mem0:add:data}}` or `{{mem0:search:query}}` template extension, which would call the `Mem0Adapter`.

**Test Specifications:**

```python
# backend/tests/adapters/test_mem0_adapter.py (Largely unchanged)
from typing import Dict, Any, List, Optional

def test_mem0_adapter_add_and_search(memory_adapter: Any) -> None:
    """Test adding a memory item and searching for it via the adapter."""
    user_id: str = "mem_user_001"
    write_request = {
        "user_id": user_id,
        "text_content": "User likes classical music.",
        "metadata": {"genre_preference": "classical"}
    }
    memory_id: Optional[str] = memory_adapter.add(write_request)
    assert memory_id is not None

    query = {"user_id": user_id, "search_text": "classical music"}
    search_results: List[Any] = memory_adapter.search(query)
    assert len(search_results) > 0

# backend/tests/service_layer/test_ai_pattern_execution_service_memory.py
# Add tests here to verify patterns (e.g., 'store_memory_item', 'retrieve_user_memories')
# correctly interact with the mock_mem0_adapter (potentially via a mocked template extension
# that calls the adapter) when executed by AIPatternExecutionService.
# Example:
# def test_pattern_stores_memory_via_template_extension(
#     ai_pattern_execution_service: Any,
#     mock_mem0_adapter: Any # Injected into the template extension's context
# ):
#     pattern_name = "store_user_memory_via_extension"
#     # Assume pattern content is like: "{{mem0:add:user_id={{user_id}},text={{text_content}}}}"
#     input_vars = {"user_id": "test_user", "text_content": "test memory"}
#     ai_pattern_execution_service.execute_pattern(pattern_name, input_vars)
#     mock_mem0_adapter.add.assert_called_once_with(...) # Verify adapter was called correctly
```

### 4. NLWeb and MCP Implementation (Entrypoints, Commands/Queries, using patterns for execution)

NLWeb `/ask` might be a Query. Actions triggered via MCP might be Commands. Both would ultimately invoke specific patterns via `AIPatternExecutionService` for complex tool execution or reasoning.

**Test Specifications:**

```python
# backend/tests/entrypoints/api/routes/test_nlweb_mcp.py
def test_mcp_tool_execution_invokes_ai_pattern(
    client: TestClient,
    mock_ai_pattern_execution_service: Any # Mock the AIPatternExecutionService
) -> None:
    """Test that executing an MCP tool invokes the correct pattern via the internal engine."""
    tool_payload: Dict[str, Any] = {
        "tool_name": "create_user_summary_mcp",
        "parameters": {"user_id": "mcp_user_123"}
    }
    # Setup mock_ai_pattern_execution_service.execute_pattern
    mock_ai_pattern_execution_service.execute_pattern.return_value = {"summary": "User is active."}

    response = client.post("/mcp/execute", json=tool_payload) # Assuming this endpoint dispatches a command
    assert response.status_code == 200
    mock_ai_pattern_execution_service.execute_pattern.assert_called_once_with(
        pattern_name="generate_user_summary_from_mcp", # Or similar pattern name
        input_variables=tool_payload["parameters"]
        # Potentially also pass output_model if structure is expected
    )
    assert response.json() == {"summary": "User is active."}
```

## Implementation Plan (TDD Cycle for each step)

### Step 1: Core Architectural Setup
(Focus on `core/`, base UoW/MessageBus interfaces in `service_layer/`, and their initial adapter implementations)

### Step 2: Internal Fabric-Inspired Engine Setup (Core Services)
**Tests:**
-   `backend/tests/service_layer/test_pattern_service.py`
-   `backend/tests/service_layer/test_template_service.py`
-   `backend/tests/service_layer/test_strategy_service.py`
-   `backend/tests/service_layer/test_context_service.py`
-   `backend/tests/service_layer/test_ai_provider_service.py`
-   `backend/tests/service_layer/test_ai_pattern_execution_service.py`
**Implementation:**
-   Services in `backend/src/app/service_layer/`
-   `Conversation` Aggregate in `backend/src/app/domain/agent/models.py` and `AbstractConversationRepository` (interface likely in `domain/agent/ports.py` or `service_layer/ports.py`).
-   `patterns/`, `strategies/`, `contexts/` directories.

### Step 3: Memory System
**Domain:** `backend/src/app/domain/memory/models.py` and `events.py`.
**Adapters:** `backend/src/app/adapters/mem0_adapter.py`.
**Commands/Queries/Handlers:** In `service_layer/commands/memory_commands.py`, `queries/memory_queries.py`, `command_handlers/memory_handlers.py`, `query_handlers/memory_query_handlers.py`.
**Tests:** In corresponding test directories.

### Step 4: FastAPI OpenAI-Compatible Endpoints
**Entrypoints:** `backend/src/app/entrypoints/api/routes/openai_compat.py`.
**Commands/Handlers:** For chat in `service_layer/commands/chat_commands.py` and `command_handlers/chat_handlers.py`.
**Tests:** `backend/tests/entrypoints/api/routes/test_openai_compat.py`, `backend/tests/service_layer/command_handlers/test_chat_handlers.py`.

### Step 5: NLWeb and MCP (Entrypoints, Commands/Queries, Patterns for execution)

Follow TDD: Define domain concepts. Test and implement patterns for NLWeb/MCP actions. Command/query handlers will invoke these patterns via `AIPatternExecutionService`. Entrypoints dispatch to handlers.

### Step 6-10: Remaining Components & Advanced Pattern Development

- **Step 6:** ActivePieces Integration (Tools callable as template extensions or orchestrated by patterns)
- **Step 7:** Google Application Development Kit (ADK) (If it provides tools or services, integrate them to be callable as template extensions or orchestrated by patterns)
- **Step 8: Custom Pattern Development & Integration**
  - Focus: Develop and integrate a suite of custom patterns for common AI tasks within the `vibeconomics` domain (e.g., advanced data analysis, content generation, complex decision making, tool chaining). These patterns will reside in `backend/src/app/patterns/` and be callable via `AIPatternExecutionService`.
- **Step 9:** CopilotKit Integration (Frontend components interacting with backend services, which use the internal engine)
- **Step 10: Advanced AI Workflow Orchestration with Internal Engine**
  - Focus: Implement complex, multi-step AI workflows using the internal engine as the primary orchestration mechanism. This involves chaining multiple patterns, incorporating conditional logic within patterns or orchestration logic, and robustly integrating with external tools (via template extensions) and data sources.

Continue the TDD cycle for each, integrating them as adapters whose functionalities are exposed and orchestrated through patterns executed by the internal engine.

## Expected Directory Structure (Backend Focus, with internal engine)

```
vibeconomics/
├── backend/
│   ├── src/
│   │   └── app/
│   │       ├── adapters/
│   │       │   ├── __init__.py
│   │       │   ├── mem0_adapter.py
│   │       │   ├── activepieces_adapter.py # Example
│   │       │   ├── nlweb_adapter.py        # Example
│   │       │   ├── uow_sqlmodel.py
│   │       │   ├── message_bus_redis.py
│   │       │   └── conversation_repository_sqlmodel.py # Example ConversationRepository impl
│   │       ├── core/
│   │       │   ├── __init__.py
│   │       │   ├── config.py
│   │       │   ├── base_aggregate.py
│   │       │   └── base_event.py
│   │       ├── domain/
│   │       │   ├── __init__.py
│   │       │   ├── chat/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── models.py
│   │       │   │   └── events.py
│   │       │   ├── memory/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── models.py # E.g., MemoryItem Aggregate
│   │       │   │   └── events.py
│   │       │   └── agent/
│   │       │       ├── __init__.py
│   │       │       ├── models.py # E.g., Conversation Aggregate
│   │       │       └── events.py
│   │       ├── entrypoints/
│   │       │   ├── __init__.py
│   │       │   └── api/
│   │       │       ├── __init__.py
│   │       │       ├── dependencies.py
│   │       │       ├── main.py
│   │       │       └── routes/
│   │       │           ├── __init__.py
│   │       │           ├── openai_compat.py
│   │       │           ├── nlweb_mcp.py
│   │       │           ├── agent_commands_api.py # Renamed for clarity if these are API routes
│   │       │           └── agent_queries_api.py  # Renamed for clarity
│   │       ├── patterns/
│   │       │   ├── __init__.py
│   │       │   ├── chat.md
│   │       │   └── summarize_text.md
│   │       ├── strategies/
│   │       │   ├── __init__.py
│   │       │   └── chain_of_thought.json
│   │       ├── contexts/
│   │       │   ├── __init__.py
│   │       │   └── project_guidelines.txt
│   │       └── service_layer/
│   │           ├── __init__.py
│   │           ├── unit_of_work.py # AbstractUoW interface
│   │           ├── message_bus.py  # AbstractMessageBus interface
│   │           ├── pattern_service.py
│   │           ├── template_service.py
│   │           ├── strategy_service.py
│   │           ├── context_service.py
│   │           ├── ai_provider_service.py
│   │           ├── ai_pattern_execution_service.py
│   │           ├── commands/
│   │           │   ├── __init__.py
│   │           │   ├── chat_commands.py
│   │           │   └── memory_commands.py
│   │           ├── queries/
│   │           │   ├── __init__.py
│   │           │   └── memory_queries.py
│   │           ├── command_handlers/
│   │           │   ├── __init__.py
│   │           │   ├── chat_handlers.py
│   │           │   └── memory_handlers.py
│   │           ├── query_handlers/
│   │           │   ├── __init__.py
│   │           │   └── memory_query_handlers.py # Clarified name
│   │           ├── event_handlers/
│   │           │   ├── __init__.py
│   │           │   └── chat_event_handlers.py
│   │           ├── llm_services.py      # For DSPy/Outlines utilities if needed
│   │           └── workflow_services.py # For non-pattern complex orchestrations
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── adapters/
│       │   └── test_mem0_adapter.py
│       ├── domain/
│       │   ├── chat/
│       │   ├── memory/
│       │   └── agent/
│       ├── entrypoints/
│       │   └── api/
│       │       └── routes/
│       │           ├── test_openai_compat.py
│       │           └── test_nlweb_mcp.py
│       ├── patterns/
│       │   └── test_example_patterns.py # Example
│       ├── service_layer/
│       │   ├── __init__.py
│       │   ├── test_pattern_service.py
│       │   ├── test_template_service.py
│       │   ├── test_strategy_service.py
│       │   ├── test_context_service.py
│       │   ├── test_ai_provider_service.py
│       │   ├── test_ai_pattern_execution_service.py
│       │   ├── commands/
│       │   │   └── test_chat_commands_structure.py # Example for command definitions
│       │   ├── command_handlers/
│       │   │   ├── test_chat_handlers.py
│       │   │   └── test_memory_handlers.py
│       │   ├── query_handlers/
│       │   │   └── test_memory_query_handlers.py
│       │   ├── event_handlers/
│       │   │   └── test_chat_event_handlers.py
│       │   └── test_llm_services.py # If llm_services.py is used
│       └── e2e/
│           └── test_e2e_pattern_workflows.py

```

## Critical End-to-End Test Cases (Focus on Internal Engine Orchestration)

### 1. E2E API Call Invoking Pattern Execution, Data Persistence, and Event Publishing

```python
# backend/tests/e2e/test_e2e_pattern_workflows.py
from fastapi.testclient import TestClient
from typing import Dict, Any, List

def test_api_invokes_pattern_saves_via_uow_and_publishes_event(
    client: TestClient,
    in_memory_message_bus: Any, # Assuming a testable in-memory message bus
    # mock_external_tool_if_pattern_uses_one: Any # Mock external dependencies
) -> None:
    """
    Test an API endpoint that triggers a pattern execution via AIPatternExecutionService,
    which in turn uses domain services, persists data (e.g., Conversation aggregate)
    via UoW, and results in a domain event being published.
    """
    # Example: An API call to analyze text and store insights using a pattern
    request_payload: Dict[str, Any] = {
        "pattern_name": "analyze_and_store_insights",
        "input_variables": {
            "text_to_analyze": "This is some complex text requiring AI analysis.",
            "user_id": "e2e_user_001"
        },
        "session_id": "optional_session_id_e2e" # To test session continuation
    }
    # This endpoint would call AIPatternExecutionService.execute_pattern
    response = client.post("/execute-ai-pattern", json=request_payload) # Example endpoint
    assert response.status_code == 200 # Or 201 if creating a new resource

    response_data = response.json()
    assert "analysis_id" in response_data # Or some other indicator of success from pattern output

    # Check that the relevant domain event was published (e.g., TextAnalysisCompletedEvent)
    # published_events = in_memory_message_bus.get_published_events()
    # assert any(isinstance(event, TextAnalysisCompletedEvent) for event in published_events)

    # Optionally, verify data persistence (e.g., Conversation aggregate updated/created)
    # (e.g., fetch the Conversation by session_id and check its messages)
```

## Additional Requirements and Guidelines

### Technology Stack Requirements

- **Python 3.11+** with strict type hints
- **FastAPI** for REST API endpoints
- **SQLModel** for database ORM (if using SQL database)
- **Pydantic** for data validation and serialization
- **pytest** for testing framework
- **LiteLLM** for unified LLM provider access.
- **DSPy** for advanced prompt engineering (used by `AIProviderService` or within pattern logic).
- **Outlines** for structured LLM output generation/validation (used by `AIProviderService` or within pattern logic).
- **Redis** for message bus (recommended)
- **Jinja2** (or similar) for the `TemplateService` (optional, can be custom).

### Code Quality Standards

1. **Type Safety**
2. **Test Coverage (>90%)**
3. **Documentation**
4. **Error Handling**
5. **Logging**
6. **Security**
7. **Performance**

### Integration Points

- **LibreChat:** OpenAI-compatible API endpoints, powered by the internal `AIPatternExecutionService`.
- **Internal Fabric-Inspired Engine:** Orchestrating AI tasks, tool usage (via template extensions), and complex workflows using patterns, strategies, contexts, and the `AIProviderService` (LiteLLM, DSPy, Outlines).
- **Mem0:** Memory persistence and retrieval, accessed via adapters used as template extensions or directly by patterns.
- **ActivePieces, NLWeb, MCP, Google ADK, CopilotKit:** Integrated as tools callable via template extensions within patterns, or their logic encapsulated within specific patterns, all orchestrated by the `AIPatternExecutionService`.

Focus on writing tests first, then implement the necessary code for the internal engine and its integration within the `vibeconomics` hexagonal architecture.

## Success Criteria

1. All tests pass with >90% coverage.
2. Complete type checking with mypy.
3. LibreChat integration working, powered by the internal AI engine.
4. Memory system functional, with interactions orchestrated by patterns via the internal engine.
5. **Internal Fabric-inspired orchestration engine (PatternService, TemplateService, StrategyService, ContextService, AIProviderService with LiteLLM/DSPy/Outlines, AIPatternExecutionService) successfully implemented and tested.**
6. All architectural patterns (Hexagonal, CQRS, DDD, UoW, Message Bus, DI) properly implemented.
7. Clean, maintainable, and well-documented codebase, including pattern, strategy, and context definitions.
8. End-to-end workflows demonstrating agentic capabilities orchestrated by the internal engine.



---
