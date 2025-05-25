#!/bin/bash

# Script to build out the Vibeconomics project structure idempotently.
# Run this script from the root of your 'vibeconomics' project.

echo "Starting Vibeconomics project setup..."

# --- Helper Functions ---

# Creates a Python file and adds initial content if the file is new or empty.
# Ensures __init__.py exists in the same directory.
create_py_file() {
    local filepath="$1"
    local imports_content="$2"
    # Ensure directory exists
    mkdir -p "$(dirname "$filepath")"

    if [ ! -f "$filepath" ]; then
        # File does not exist, create it and add imports
        echo -e "$imports_content" > "$filepath"
        echo "CREATED and INITIALIZED: $filepath"
    else
        # File exists. If it's empty, add imports. Otherwise, leave it.
        if [ ! -s "$filepath" ]; then # -s checks if file exists and has size > 0
            echo -e "$imports_content" > "$filepath"
            echo "INITIALIZED empty existing file: $filepath"
        else
            echo "EXISTS (not empty, content not modified): $filepath"
        fi
    fi

    # Always create __init__.py in the same directory if it's a Python package dir
    # And if the current file is not __init__.py itself
    local dir_path="$(dirname "$filepath")"
    if [[ "$filepath" == *.py && "$(basename "$filepath")" != "__init__.py" ]]; then
        create_py_file_minimal "$dir_path/__init__.py"
    fi
}

# Creates a file (typically __init__.py or non-Python files) if it doesn't exist.
# Does not add content beyond touching the file.
create_py_file_minimal() {
    local filepath="$1"
    mkdir -p "$(dirname "$filepath")"
    if [ ! -f "$filepath" ]; then
        touch "$filepath"
        echo "CREATED: $filepath"
    else
        echo "EXISTS: $filepath"
    fi
}

# --- Base Directory ---
mkdir -p backend/src/app
mkdir -p backend/tests

# --- backend/src/app ---

# Adapters
adapters_imports_common="from typing import Dict, Any, List, Optional, Type, Callable, AsyncGenerator\nfrom uuid import UUID\nfrom pydantic import BaseModel, Field\nfrom abc import ABC, abstractmethod\nfrom typing import Protocol"
create_py_file "backend/src/app/adapters/__init__.py" ""
create_py_file "backend/src/app/adapters/mem0_adapter.py" "$adapters_imports_common\n# import mem0\n# from app.domain.memory.models import MemoryWriteRequest, MemoryQueryResult"
create_py_file "backend/src/app/adapters/activepieces_adapter.py" "$adapters_imports_common"
create_py_file "backend/src/app/adapters/nlweb_adapter.py" "$adapters_imports_common"
create_py_file "backend/src/app/adapters/uow_sqlmodel.py" "$adapters_imports_common\n# from sqlalchemy.ext.asyncio import AsyncSession\n# from app.service_layer.unit_of_work import AbstractUnitOfWork, AbstractRepository"
create_py_file "backend/src/app/adapters/message_bus_redis.py" "$adapters_imports_common\n# import redis.asyncio as redis\n# from app.core.base_aggregate import DomainEvent\n# from app.service_layer.message_bus import AbstractMessageBus, EventHandlersMap"
create_py_file "backend/src/app/adapters/conversation_repository_sqlmodel.py" "$adapters_imports_common\n# from sqlalchemy.ext.asyncio import AsyncSession\n# from app.domain.agent.models import Conversation\n# from app.domain.agent.ports import AbstractConversationRepository # Define in domain/agent/ports.py"

# Core
core_imports_common="from typing import List, TypeVar, Generic, Optional\nfrom uuid import UUID, uuid4\nfrom pydantic import BaseModel, Field"
create_py_file "backend/src/app/core/__init__.py" ""
create_py_file "backend/src/app/core/config.py" "from pydantic_settings import BaseSettings, SettingsConfigDict\n\nclass Settings(BaseSettings):\n    APP_NAME: str = \"Vibeconomics Agentic Framework\"\n    # EXAMPLE_API_KEY: str = \"your_api_key_here\"\n\n    model_config = SettingsConfigDict(env_file=\".env\", extra=\"ignore\")\n\nsettings = Settings()"
create_py_file "backend/src/app/core/base_aggregate.py" "$core_imports_common\n\nclass DomainEvent(BaseModel):\n    event_id: UUID = Field(default_factory=uuid4)\n    # Add other common event fields like timestamp\n\nT = TypeVar('T')\n\nclass AggregateRoot(BaseModel, Generic[T]):\n    id: T = Field(default_factory=lambda: uuid4() if T is UUID else None) # type: ignore\n    version: int = 1\n    _events: List[DomainEvent] = Field(default_factory=list, exclude=True) # exclude from model dump by default\n\n    def add_event(self, event: DomainEvent) -> None:\n        self._events.append(event)\n\n    def pull_events(self) -> List[DomainEvent]:\n        events = list(self._events)\n        self._events.clear()\n        return events\n\n    class Config:\n        arbitrary_types_allowed = True"
create_py_file "backend/src/app/core/base_event.py" "# This file can be used for more specific base event classes if needed.\n# DomainEvent is currently in base_aggregate.py"

# Domain
domain_imports_common="from typing import List, Optional, Dict, Any\nfrom uuid import UUID, uuid4\nfrom pydantic import BaseModel, Field\nfrom app.core.base_aggregate import AggregateRoot, DomainEvent"

create_py_file "backend/src/app/domain/__init__.py" ""
# Domain - Chat
create_py_file "backend/src/app/domain/chat/__init__.py" ""
create_py_file "backend/src/app/domain/chat/models.py" "$domain_imports_common"
create_py_file "backend/src/app/domain/chat/events.py" "$domain_imports_common"
# Domain - Memory
create_py_file "backend/src/app/domain/memory/__init__.py" ""
create_py_file "backend/src/app/domain/memory/models.py" "$domain_imports_common\n\nclass MemoryItem(AggregateRoot[UUID]):\n    user_id: str\n    text_content: str\n    metadata: Optional[Dict[str, Any]] = None\n\nclass MemoryWriteRequest(BaseModel):\n    user_id: str\n    text_content: str\n    metadata: Optional[Dict[str, Any]] = None\n\nclass MemoryQueryResultItem(BaseModel):\n    id: str\n    text: str\n    metadata: Optional[Dict[str, Any]] = None\n    score: Optional[float] = None\n\nclass MemoryQueryResult(BaseModel):\n    results: List[MemoryQueryResultItem]"
create_py_file "backend/src/app/domain/memory/events.py" "$domain_imports_common\n\nclass MemoryStoredEvent(DomainEvent):\n    memory_id: str\n    user_id: str"
# Domain - Agent
create_py_file "backend/src/app/domain/agent/__init__.py" ""
create_py_file "backend/src/app/domain/agent/models.py" "$domain_imports_common\n\nclass ChatMessage(BaseModel):\n    role: str # \"user\", \"assistant\", \"system\"\n    content: str\n\nclass Conversation(AggregateRoot[UUID]):\n    # id is inherited from AggregateRoot\n    user_id: Optional[str] = None\n    messages: List[ChatMessage] = Field(default_factory=list)\n    # created_at: datetime = Field(default_factory=datetime.utcnow)\n    # last_updated_at: datetime = Field(default_factory=datetime.utcnow)\n\n    def add_message(self, role: str, content: str) -> None:\n        msg = ChatMessage(role=role, content=content)\n        self.messages.append(msg)\n        # self.add_event(ConversationMessageAddedEvent(conversation_id=self.id, role=role, content_preview=content[:50]))"
create_py_file "backend/src/app/domain/agent/events.py" "$domain_imports_common\n\nclass ConversationMessageAddedEvent(DomainEvent):\n    conversation_id: UUID\n    role: str\n    content_preview: str"
create_py_file "backend/src/app/domain/agent/ports.py" "from typing import Protocol, Optional\nfrom uuid import UUID\nfrom .models import Conversation # Relative import\n\nclass AbstractConversationRepository(Protocol):\n    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]: ...\n    async def save(self, conversation: Conversation) -> None: ...\n    async def add(self, conversation: Conversation) -> None: ... # Alias for save or specific create"


# Entrypoints
entrypoints_imports_common="from fastapi import APIRouter, HTTPException, Body, Depends, Request, Query, Path\nfrom fastapi.responses import StreamingResponse, JSONResponse\nfrom typing import List, Dict, Any, AsyncGenerator, Union, Optional\nfrom uuid import UUID\nfrom pydantic import BaseModel, Field\nimport json\nimport asyncio"
create_py_file "backend/src/app/entrypoints/__init__.py" ""
create_py_file "backend/src/app/entrypoints/api/__init__.py" ""
create_py_file "backend/src/app/entrypoints/api/dependencies.py" "$entrypoints_imports_common\n# from sqlalchemy.ext.asyncio import AsyncSession # Example\n# from app.adapters.uow_sqlmodel import SqlModelUnitOfWork\n# from app.service_layer.unit_of_work import AbstractUnitOfWork\n# from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService\n# from app.service_layer.pattern_service import PatternService\n# ... other services and repositories"
create_py_file "backend/src/app/entrypoints/api/main.py" "$entrypoints_imports_common\nfrom fastapi import FastAPI\n# from .routes import openai_compat, nlweb_mcp, agent_commands_api, agent_queries_api # Example\n# from .dependencies import setup_dependencies # Example\n\napp = FastAPI(title=\"Vibeconomics Agentic Framework\")\n\n# Example: setup_dependencies(app)\n\n# Example: app.include_router(openai_compat.router)\n\n@app.get(\"/\")\nasync def root():\n    return {\"message\": \"Welcome to Vibeconomics Agentic Framework\"}"
# Entrypoints - Routes
create_py_file "backend/src/app/entrypoints/api/routes/__init__.py" ""
create_py_file "backend/src/app/entrypoints/api/routes/openai_compat.py" "$entrypoints_imports_common\n\nrouter = APIRouter(prefix=\"/v1/chat\", tags=[\"OpenAI Compatible Chat\"])\n\n# @router.post(\"/completions\")\n# async def create_chat_completion(): ... "
create_py_file "backend/src/app/entrypoints/api/routes/nlweb_mcp.py" "$entrypoints_imports_common\n\nrouter = APIRouter(prefix=\"/tools\", tags=[\"NLWeb & MCP\"])\n\n# @router.post(\"/nlweb/ask\")\n# async def nlweb_ask(): ...\n# @router.post(\"/mcp/execute\")\n# async def mcp_execute(): ..."
create_py_file "backend/src/app/entrypoints/api/routes/agent_commands_api.py" "$entrypoints_imports_common\n\nrouter = APIRouter(prefix=\"/agent/commands\", tags=[\"Agent Commands\"])\n\n# @router.post(\"/execute-pattern\")\n# async def execute_pattern(): ..."
create_py_file "backend/src/app/entrypoints/api/routes/agent_queries_api.py" "$entrypoints_imports_common\n\nrouter = APIRouter(prefix=\"/agent/queries\", tags=[\"Agent Queries\"])\n"

# Patterns, Strategies, Contexts (non-Python files, just create dirs and example files)
mkdir -p backend/src/app/patterns
create_py_file_minimal "backend/src/app/patterns/__init__.py" # For Python to see it as a potential resource package
create_py_file_minimal "backend/src/app/patterns/chat.md" "# Example Chat Pattern\n\nUser: {{input}}\nAssistant:"
create_py_file_minimal "backend/src/app/patterns/summarize_text.md" "# Example Summarize Pattern\n\nSummarize the following text:\n\n{{input}}\n\nSummary:"

mkdir -p backend/src/app/strategies
create_py_file_minimal "backend/src/app/strategies/__init__.py"
create_py_file_minimal "backend/src/app/strategies/chain_of_thought.json" "{\n  \"name\": \"chain_of_thought\",\n  \"description\": \"Chain-of-Thought (CoT) Prompting\",\n  \"prompt\": \"Think step by step to answer the question. Return the final answer in the required format.\"\n}"

mkdir -p backend/src/app/contexts
create_py_file_minimal "backend/src/app/contexts/__init__.py"
create_py_file_minimal "backend/src/app/contexts/project_guidelines.txt" "These are the project guidelines..."

# Service Layer
service_layer_imports_common="from typing import List, Dict, Any, Optional, Type, Callable, AsyncGenerator, Protocol\nfrom uuid import UUID\nfrom pydantic import BaseModel, Field\nfrom abc import ABC, abstractmethod\nfrom app.core.base_aggregate import DomainEvent # Adjusted import"

create_py_file "backend/src/app/service_layer/__init__.py" ""
create_py_file "backend/src/app/service_layer/unit_of_work.py" "$service_layer_imports_common\n\nclass AbstractRepository(Protocol):\n    async def add(self, entity: Any) -> None: ...\n    async def get(self, id: Any) -> Optional[Any]: ...\n    # Add other common repository methods like list, delete, update\n\nclass AbstractUnitOfWork(Protocol):\n    # repositories: Dict[str, AbstractRepository] # Or specific ones\n    async def __aenter__(self) -> 'AbstractUnitOfWork': ...\n    async def __aexit__(self, exc_type: Any, exc_val: Any, traceback: Any) -> None: ...\n    async def commit(self) -> None: ...\n    async def rollback(self) -> None: ...\n    # def get_repository(self, repo_name: str) -> AbstractRepository: ..."
create_py_file "backend/src/app/service_layer/message_bus.py" "$service_layer_imports_common\n\nEventHandlersMap = Dict[Type[DomainEvent], List[Callable[..., Any]]]\n\nclass AbstractMessageBus(Protocol):\n    event_handlers: EventHandlersMap\n\n    async def publish(self, event: DomainEvent) -> None: ...\n    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[..., Any]) -> None: ..."

# Service Layer - Engine Components
create_py_file "backend/src/app/service_layer/pattern_service.py" "$service_layer_imports_common\nfrom pathlib import Path\n\nclass PatternNotFoundError(Exception):\n    pass"
create_py_file "backend/src/app/service_layer/template_service.py" "$service_layer_imports_common\n\nclass MissingVariableError(Exception):\n    pass\n\nclass TemplateExtensionError(Exception):\n    pass"
create_py_file "backend/src/app/service_layer/strategy_service.py" "$service_layer_imports_common\n\nclass Strategy(BaseModel):\n    name: str\n    description: str\n    prompt: str\n\nclass StrategyNotFoundError(Exception):\n    pass\n\nclass InvalidStrategyFormatError(Exception):\n    pass"
create_py_file "backend/src/app/service_layer/context_service.py" "$service_layer_imports_common\nfrom pathlib import Path\n\nclass ContextNotFoundError(Exception):\n    pass"
create_py_file "backend/src/app/service_layer/ai_provider_service.py" "$service_layer_imports_common\n# import litellm"
create_py_file "backend/src/app/service_layer/ai_pattern_execution_service.py" "$service_layer_imports_common\n# from .pattern_service import PatternService\n# from .template_service import TemplateService\n# ... other engine service imports\n# from app.domain.agent.ports import AbstractConversationRepository"

# Service Layer - CQRS
create_py_file "backend/src/app/service_layer/commands/__init__.py" ""
create_py_file "backend/src/app/service_layer/commands/chat_commands.py" "$service_layer_imports_common\n\nclass ProcessUserChatMessageCommand(BaseModel):\n    session_id: Optional[UUID] = None\n    user_id: Optional[str] = None\n    message_content: str\n    model_name: Optional[str] = None\n    # Add other relevant fields"
create_py_file "backend/src/app/service_layer/commands/memory_commands.py" "$service_layer_imports_common\n\nclass StoreMemoryCommand(BaseModel):\n    user_id: str\n    text_content: str\n    metadata: Optional[Dict[str, Any]] = None"

create_py_file "backend/src/app/service_layer/queries/__init__.py" ""
create_py_file "backend/src/app/service_layer/queries/memory_queries.py" "$service_layer_imports_common\n# from app.domain.memory.models import MemoryQueryResult\n\nclass SearchMemoryQuery(BaseModel):\n    user_id: str\n    search_text: str\n    limit: int = 10"

create_py_file "backend/src/app/service_layer/command_handlers/__init__.py" ""
create_py_file "backend/src/app/service_layer/command_handlers/chat_handlers.py" "$service_layer_imports_common\n# from ..commands.chat_commands import ProcessUserChatMessageCommand\n# from ..ai_pattern_execution_service import AIPatternExecutionService\n# from ..unit_of_work import AbstractUnitOfWork"
create_py_file "backend/src/app/service_layer/command_handlers/memory_handlers.py" "$service_layer_imports_common\n# from ..commands.memory_commands import StoreMemoryCommand\n# from app.domain.memory.ports import AbstractMemoryRepository # Define in domain/memory/ports.py\n# from ..unit_of_work import AbstractUnitOfWork\n# from ..message_bus import AbstractMessageBus"

create_py_file "backend/src/app/service_layer/query_handlers/__init__.py" ""
create_py_file "backend/src/app/service_layer/query_handlers/memory_query_handlers.py" "$service_layer_imports_common\n# from ..queries.memory_queries import SearchMemoryQuery\n# from app.domain.memory.models import MemoryQueryResult\n# from app.domain.memory.ports import AbstractMemoryRepository"

create_py_file "backend/src/app/service_layer/event_handlers/__init__.py" ""
create_py_file "backend/src/app/service_layer/event_handlers/chat_event_handlers.py" "$service_layer_imports_common\n# from app.domain.chat.events import SomeChatEvent"

# Service Layer - Other Services
create_py_file "backend/src/app/service_layer/llm_services.py" "$service_layer_imports_common\n# For DSPy/Outlines utilities if needed, or specific LLM interaction logic"
create_py_file "backend/src/app/service_layer/workflow_services.py" "$service_layer_imports_common\n# For non-pattern based complex orchestrations, if any"


# --- backend/tests ---
tests_imports_common="import pytest\nfrom unittest.mock import AsyncMock, MagicMock, patch\nfrom typing import List, Dict, Any, Optional, Type, Callable, AsyncGenerator\nfrom uuid import UUID, uuid4\nfrom pydantic import BaseModel, Field"

create_py_file "backend/tests/__init__.py" ""
create_py_file "backend/tests/conftest.py" "$tests_imports_common\n# from fastapi.testclient import TestClient\n# from app.entrypoints.api.main import app # Assuming main.py has the FastAPI app\n\n# @pytest.fixture(scope=\"session\")\n# def client() -> TestClient:\n#     return TestClient(app)\n\n# @pytest.fixture\n# def mock_uow() -> MagicMock:\n#     return MagicMock(spec=AbstractUnitOfWork)\n\n# @pytest.fixture\n# def mock_message_bus() -> MagicMock:\n#     return MagicMock(spec=AbstractMessageBus)"

# Tests - Adapters
create_py_file "backend/tests/adapters/__init__.py" ""
create_py_file "backend/tests/adapters/test_mem0_adapter.py" "$tests_imports_common\n# from app.adapters.mem0_adapter import Mem0Adapter"
create_py_file "backend/tests/adapters/test_conversation_repository_inmemory.py" "$tests_imports_common\n# from app.adapters.conversation_repository_inmemory import InMemoryConversationRepository\n# from app.domain.agent.models import Conversation, ChatMessage"


# Tests - Domain
create_py_file "backend/tests/domain/__init__.py" ""
create_py_file "backend/tests/domain/test_core_models.py" "$tests_imports_common\nfrom app.core.base_aggregate import AggregateRoot, DomainEvent"
create_py_file "backend/tests/domain/chat/__init__.py" ""
create_py_file "backend/tests/domain/chat/test_chat_models.py" "$tests_imports_common\n# from app.domain.chat.models import YourChatModel"
create_py_file "backend/tests/domain/memory/__init__.py" ""
create_py_file "backend/tests/domain/memory/test_memory_models.py" "$tests_imports_common\n# from app.domain.memory.models import MemoryItem"
create_py_file "backend/tests/domain/agent/__init__.py" ""
create_py_file "backend/tests/domain/agent/test_agent_models.py" "$tests_imports_common\n# from app.domain.agent.models import Conversation, ChatMessage"

# Tests - Entrypoints
create_py_file "backend/tests/entrypoints/__init__.py" ""
create_py_file "backend/tests/entrypoints/api/__init__.py" ""
create_py_file "backend/tests/entrypoints/api/routes/__init__.py" ""
create_py_file "backend/tests/entrypoints/api/routes/test_openai_compat.py" "$tests_imports_common\n# from fastapi.testclient import TestClient"
create_py_file "backend/tests/entrypoints/api/routes/test_nlweb_mcp.py" "$tests_imports_common\n# from fastapi.testclient import TestClient"
create_py_file "backend/tests/entrypoints/api/routes/test_agent_commands_api.py" "$tests_imports_common\n# from fastapi.testclient import TestClient"


# Tests - Patterns (example, might not need specific tests for .md files unless testing loading logic)
create_py_file "backend/tests/patterns/__init__.py" ""
create_py_file "backend/tests/patterns/test_example_patterns.py" "$tests_imports_common\n# Test pattern loading or specific complex pattern logic if applicable"

# Tests - Service Layer
create_py_file "backend/tests/service_layer/__init__.py" ""
create_py_file "backend/tests/service_layer/test_abstractions.py" "$tests_imports_common\n# from app.service_layer.unit_of_work import AbstractUnitOfWork\n# from app.service_layer.message_bus import AbstractMessageBus"
create_py_file "backend/tests/service_layer/test_pattern_service.py" "$tests_imports_common\n# from app.service_layer.pattern_service import PatternService, PatternNotFoundError"
create_py_file "backend/tests/service_layer/test_template_service.py" "$tests_imports_common\n# from app.service_layer.template_service import TemplateService, MissingVariableError"
create_py_file "backend/tests/service_layer/test_strategy_service.py" "$tests_imports_common\n# from app.service_layer.strategy_service import StrategyService, Strategy, StrategyNotFoundError"
create_py_file "backend/tests/service_layer/test_context_service.py" "$tests_imports_common\n# from app.service_layer.context_service import ContextService, ContextNotFoundError"
create_py_file "backend/tests/service_layer/test_ai_provider_service.py" "$tests_imports_common\n# from app.service_layer.ai_provider_service import AIProviderService"
create_py_file "backend/tests/service_layer/test_ai_pattern_execution_service.py" "$tests_imports_common\n# from app.service_layer.ai_pattern_execution_service import AIPatternExecutionService"
create_py_file "backend/tests/service_layer/test_conversation_repository.py" "$tests_imports_common\n# from app.domain.agent.ports import AbstractConversationRepository"


# Tests - Service Layer - CQRS
create_py_file "backend/tests/service_layer/commands/__init__.py" ""
create_py_file "backend/tests/service_layer/commands/test_chat_commands_structure.py" "$tests_imports_common\n# from app.service_layer.commands.chat_commands import ProcessUserChatMessageCommand"
create_py_file "backend/tests/service_layer/command_handlers/__init__.py" ""
create_py_file "backend/tests/service_layer/command_handlers/test_chat_handlers.py" "$tests_imports_common\n# from app.service_layer.command_handlers.chat_handlers import ProcessUserChatMessageCommandHandler"
create_py_file "backend/tests/service_layer/command_handlers/test_memory_handlers.py" "$tests_imports_common\n# from app.service_layer.command_handlers.memory_handlers import StoreMemoryCommandHandler"
create_py_file "backend/tests/service_layer/query_handlers/__init__.py" ""
create_py_file "backend/tests/service_layer/query_handlers/test_memory_query_handlers.py" "$tests_imports_common\n# from app.service_layer.query_handlers.memory_query_handlers import SearchMemoryQueryHandler"
create_py_file "backend/tests/service_layer/event_handlers/__init__.py" ""
create_py_file "backend/tests/service_layer/event_handlers/test_chat_event_handlers.py" "$tests_imports_common\n# from app.service_layer.event_handlers.chat_event_handlers import SomeChatEventHandler"

# Tests - Service Layer - Other Services
create_py_file "backend/tests/service_layer/test_llm_services.py" "$tests_imports_common\n# from app.service_layer.llm_services import YourLLMUtilityClass"

# Tests - E2E
create_py_file "backend/tests/e2e/__init__.py" ""
create_py_file "backend/tests/e2e/test_e2e_pattern_workflows.py" "$tests_imports_common\n# from fastapi.testclient import TestClient"

# --- Root project files (examples) ---
create_py_file_minimal ".gitignore" "*.pyc\n__pycache__/\n.env\nvenv/\n*.db\n*.sqlite3\ninstance/\n.pytest_cache/\n.mypy_cache/\nbuild/\ndist/\n*.egg-info/"
create_py_file_minimal "README.md" "# Vibeconomics Agentic Framework\n\nThis is the main README file."
create_py_file_minimal "requirements.txt" "fastapi\nuvicorn[standard]\npydantic\npydantic-settings\n# sqlmodel # If using SQLModel\n# redis # If using Redis\n# litellm # For AIProviderService\n# mem0 # For Mem0 integration\n# dspy-ai # For DSPy\n# outlines-dev # For Outlines\n\n# Testing\npytest\npytest-cov\npytest-asyncio\nhttpx # For TestClient"
create_py_file_minimal "pyproject.toml" "[tool.pytest.ini_options]\npythonpath = [\".\", \"backend/src\"]\nasyncio_mode = \"auto\"\n\n[tool.mypy]\npython_version = \"3.11\"\nwarn_return_any = true\nwarn_unused_configs = true\ndisallow_untyped_defs = true\ncheck_untyped_defs = true\nignore_missing_imports = true # Start with true, then refine\n# Add path for mypy if needed, e.g.\n# mypy_path = \"backend/src\"\n\n  [[tool.mypy.overrides]]\n  module = \"mem0.*\" # Example: ignore missing stubs for mem0\n  ignore_missing_imports = true\n"
create_py_file_minimal ".env.example" "EXAMPLE_API_KEY=\"your_api_key_here\"\n# LiteLLM specific keys if not managed globally by LiteLLM\n# OPENAI_API_KEY=\n# ANTHROPIC_API_KEY=\n# COHERE_API_KEY=\n\n# MEM0_API_KEY="


echo "Vibeconomics project setup script finished."
echo "Next steps:"
echo "1. Create a virtual environment: python -m venv venv"
echo "2. Activate it: source venv/bin/activate (or venv\\Scripts\\activate on Windows)"
echo "3. Install requirements: pip install -r requirements.txt"
echo "4. Copy .env.example to .env and fill in your API keys."
echo "5. Run tests: pytest"

