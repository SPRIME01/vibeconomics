# Vibeconomics: Agentic Application Framework

<a href="https://github.com/fastapi/full-stack-fastapi-template/actions?query=workflow%3ATest" target="_blank"><img src="https://github.com/fastapi/full-stack-fastapi-template/workflows/Test/badge.svg" alt="Test"></a>
<a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/fastapi/full-stack-fastapi-template" target="_blank"><img src="https://coverage-badge.samuelcolvin.workers.dev/fastapi/full-stack-fastapi-template.svg" alt="Coverage"></a>

## Project Overview

Vibeconomics is a comprehensive Agentic Application Framework built upon advanced architectural patterns. The project leverages Test-Driven Development (TDD), strict typing, and sophisticated backend architecture based on Hexagonal principles, CQRS, Domain-Driven Design (DDD) Aggregates, Unit of Work (UoW) pattern, Message Bus for domain events, and Dependency Injection (DI).

## Architecture and Design Principles

### Hexagonal Architecture (Ports and Adapters)

- **Domain Layer**: Core business logic, Aggregates, Value Objects, and Domain Events with no external dependencies
- **Service Layer**: Orchestrates use cases through Command Handlers, Query Handlers, and Event Handlers
- **Adapters Layer**: Infrastructure concerns including Repositories, Unit of Work implementation, and external service clients
- **Entrypoints Layer**: API routes (FastAPI) that primarily dispatch Commands or Queries

### Advanced Patterns Implemented

- **CQRS (Command Query Responsibility Segregation)**: Clear separation of write operations (Commands) from read operations (Queries)
- **DDD Aggregates**: Defined consistency boundaries within domain models
- **Unit of Work (UoW)**: Ensures atomicity for operations involving multiple Aggregates or Repositories
- **Message Bus**: Decouples components by publishing Domain Events when significant state changes occur
- **Dependency Injection (DI)**: FastAPI's DI used to inject dependencies into handlers and entrypoints

## Core Components

### 1. LibreChat with DSPy Backend Integration

Provides OpenAI-compatible API endpoints with custom DSPy-powered language model backends.

### 2. DSPy and Outlines Integration

Core reasoning services that enable structured outputs and sophisticated AI reasoning patterns.

### 3. Mem0 Memory System Integration

Persistent memory storage and retrieval services for AI agents.

### 4. NLWeb and MCP Implementation

Natural language web interaction capabilities and Model Context Protocol implementation.

### 5. ActivePieces Integration

Workflow automation capabilities for AI-driven processes.

### 6. Additional AI Components

- [Google Application Development Kit (ADK)](https://github.com/google/adk-python.git)
- [Fabric](https://github.com/danielmiessler/fabric.git)
- [CopilotKit](https://github.com/CopilotKit/CopilotKit.git) Integration
- Advanced AI Workflow Orchestration

## Technology Stack

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API
  - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM)
  - 🔍 [Pydantic](https://docs.pydantic.dev) for data validation and settings management
  - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database
- 🔄 [**DSPy**](https://github.com/stanfordnlp/dspy.git) for LLM reasoning chains
- 📊 [**Outlines**](https://github.com/dottxt-ai/outlines.git) for structured generation
- 🧠 [**Mem0**](https://github.com/mem0ai/mem0.git) for agent memory persistence
- 📨 [**Redis**](https://github.com/redis/redis.git) for message bus (recommended)
- 🚀 [React](https://react.dev) for the frontend
  - 💃 Using TypeScript, hooks, Vite
  - 🎨 [Chakra UI](https://chakra-ui.com) for the frontend components
  - 🤖 An automatically generated frontend client
  - 🧪 [Playwright](https://playwright.dev) for End-to-End testing
- 🐋 [Docker Compose](https://www.docker.com) for development and production
- 🔒 JWT (JSON Web Token) authentication
- ✅ Comprehensive testing with [Pytest](https://pytest.org)
- 🚢 CI/CD based on GitHub Actions

## Development Approach: Test-Driven Development & Strict Typing

This project strictly follows a Test-Driven Development workflow:

1. **Write Tests First**: Comprehensive tests using `pytest` that define expected behavior, interfaces, contracts, and emitted domain events
2. **Implement Minimal Code**: Simple production code to make tests pass
3. **Refactor**: Improve code structure and clarity while maintaining passing tests
4. **Document**: Add docstrings to all public interfaces

All Python code includes comprehensive type hints as per PEP 484, with successful mypy type checking.

## Getting Started

### How To Use It

You can **fork or clone** this repository and use it as is.

### Configure

Update configs in the `.env` files to customize your configurations.

Before deploying, make sure you change at least the values for:

- `SECRET_KEY`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_PASSWORD`

### Generate Secret Keys

To generate secret keys, you can run:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Backend Development

Backend docs: [backend/README.md](./backend/README.md).

## Frontend Development

Frontend docs: [frontend/README.md](./frontend/README.md).

## Deployment

Deployment docs: [deployment.md](./deployment.md).

## Development

General development docs: [development.md](./development.md).

## License

The Vibeconomics project is licensed under the terms of the MIT license.
