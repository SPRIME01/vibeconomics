\
# Backend Migration to Clean Architecture (Cosmic Python Style)

This document outlines the steps to migrate the backend of the Vibeconomics project to a Clean Architecture structure, following the principles from the [Cosmic Python book](https://www.cosmicpython.com/book/appendix_project_structure.html).

## Phase 1: Project Restructuring (The "Big Move")

This phase focuses on rearranging the directory structure and setting up the new layout. We will use Python scripts for file operations where possible to minimize manual errors and track changes.

**Legend:**
- `[ ]`: Task to be done
- `[x]`: Task completed
- `[-]`: Task skipped/not applicable

### 1. Preparation & Setup

*   [ ] **Version Control**: Ensure your Git working directory is clean and all changes are committed.
*   [ ] **Create Branch**: Create a new Git branch for this migration (e.g., `feature/clean-architecture-migration`).
*   [ ] **Review Dependencies**: Note current dependencies in `backend/pyproject.toml` and `backend/uv.lock`. The new structure will be a Python package.

### 2. Root Directory Restructuring for Backend

*   [ ] **Create `backend/src/` directory**: This will house the main application package.
    *   *Action*: Create directory `c:\\Users\\sprim\\FocusAreas\\Projects\\Dev\\vibeconomics\\backend\\src`.
*   [ ] **Create `backend/src/app/` directory**: This will be our main application package, moved from the current `backend/app/`.
    *   *Action*: Create directory `c:\\Users\\sprim\\FocusAreas\\Projects\\Dev\\vibeconomics\\backend\\src\\app`.
*   [ ] **Create `backend/src/setup.py`**: This file will make our `app` package installable.
    *   *Action*: Create `c:\\Users\\sprim\\FocusAreas\\Projects\\Dev\\vibeconomics\\backend\\src\\setup.py` with the following content:
        ```python
        from setuptools import setup, find_packages

        setup(
            name="app",  # Or a more specific name like "vibeconomics_api"
            version="0.1.0",
            packages=find_packages(),
            # Add other metadata as needed
        )
        ```
*   [ ] **Move `backend/app/` contents to `backend/src/app/`**:\n    *   *Source*: `c:\\Users\\sprim\\FocusAreas\\Projects\\Dev\\vibeconomics\\backend\\app\\`\n    *   *Destination*: `c:\\Users\\sprim\\FocusAreas\\Projects\\Dev\\vibeconomics\\backend\\src\\app\\`\n    *   *Files/Folders to move*:\n        *   `__init__.py`\n        *   `backend_pre_start.py`\n        *   `crud.py`\n        *   `initial_data.py`\n        *   `main.py` (FastAPI app)\n        *   `models.py`\n        *   `tests_pre_start.py`\n        *   `utils.py`\n        *   `api/` (directory)\n        *   `core/` (directory)\n        *   `email-templates/` (directory)\n        *   `alembic/` (directory containing migration scripts - we\'ll refine its place later)\n    *   *Action*: Use a Python script with `shutil.move` for each item, or move them manually carefully.
*   [ ] **Move `backend/tests/` (currently `backend/app/tests/`) to `backend/tests/`**: Tests should reside at the same level as the `src` directory.
    *   *Source*: `c:\\Users\\sprim\\FocusAreas\\Projects\\Dev\\vibeconomics\\backend\\app\\tests\\`
    *   *Destination*: `c:\\Users\\sprim\\FocusAreas\\Projects\\Dev\\vibeconomics\\backend\\tests\\`
    *   *Action*: Use `shutil.move`.

### 3. Refactor within `backend/src/app/`

This is where the core architectural changes happen.

*   **`config.py`**:\n    *   [ ] **Move and Refine**: Move `backend/src/app/core/config.py` to `backend/src/app/config.py`.\n    *   [ ] **Environment Variables**: Ensure it primarily reads from environment variables, with sensible defaults for local development (as per Cosmic Python).
*   **`domain/` layer**:\n    *   [ ] **Create Directory**: `backend/src/app/domain/`\n    *   [ ] **Move Models**: Identify pure domain models from `backend/src/app/models.py`. Move their definitions to `backend/src/app/domain/models.py` (or `model.py`). These should ideally be free of ORM-specific details. SQLModel blurs this, so focus on separating data structures from persistence logic.
*   **`adapters/` layer**:\n    *   [ ] **Create Directory**: `backend/src/app/adapters/`\n    *   [ ] **ORM (`orm.py`)**: Create `backend/src/app/adapters/orm.py`.\n        *   Define SQLModel/SQLAlchemy table metadata, mappings, and the database engine creation (from `core/db.py`).\n    *   [ ] **Repository (`repository.py`)**: Create `backend/src/app/adapters/repository.py`.\n        *   Implement repository patterns here. Much of `crud.py` will be refactored into these repositories.\n    *   [ ] **Database Initialization (`db_init.py` or similar)**: The `init_db` function from `core/db.py` might live here or be part of a bootstrap script.\n    *   [ ] **Alembic Scripts**:\n        *   Move the contents of `backend/src/app/alembic/` (which was `backend/app/alembic/`) to `backend/src/app/adapters/alembic_scripts/`.\n        *   The `alembic.ini` file (currently at `backend/alembic.ini`) will need its `script_location` updated to point to this new path (e.g., `src/app/adapters/alembic_scripts`).
*   **`service_layer/`**:\n    *   [ ] **Create Directory**: `backend/src/app/service_layer/`\n    *   [ ] **Services (`services.py`)**: Create `backend/src/app/service_layer/services.py`.\n        *   Define use cases/application services. These orchestrate domain objects and repositories.\n    *   [ ] **Unit of Work (UoW)**: Consider implementing the UoW pattern for atomic operations.\n*   **`entrypoints/` layer**:\n    *   [ ] **Create Directory**: `backend/src/app/entrypoints/`\n    *   [ ] **FastAPI App (`fastapi_app.py`)**: Move the FastAPI app instantiation from `backend/src/app/main.py` to `backend/src/app/entrypoints/fastapi_app.py`.\n    *   [ ] **API Routes**: Move `backend/src/app/api/` (routes, dependencies) into `backend/src/app/entrypoints/api/` or integrate them with `fastapi_app.py`.\n    *   [ ] **Scripts**: Refactor `backend_pre_start.py`, `initial_data.py` into entrypoint scripts or management commands if they are part of application startup or setup.

### 4. Update Imports, Configurations, and Tooling

*   [ ] **PYTHONPATH/Installation**:\n    *   Ensure the `app` package is installable. In your `backend/` directory, you should be able to run `pip install -e ./src` (or the `uv` equivalent).\n    *   Update `backend/pyproject.toml` if it specifies package locations (e.g., for Poetry: `packages = [{include = \"app\", from = \"src\"}]`).
*   [ ] **Update Imports**: This is a significant task. Go through all Python files and update import statements to reflect the new module paths (e.g., `from app.core.config import settings` might become `from app.config import settings` or `from app.adapters.orm import engine`).
*   [ ] **`backend/Dockerfile`**:\n    *   Update `COPY` commands to use the `src/` layout (e.g., `COPY ./src /app/src`).\n    *   Add a step to install the local package: `RUN pip install -e /app/src` (or `uv` equivalent).\n    *   Adjust `WORKDIR` and `CMD` / `ENTRYPOINT` as necessary.\n*   [ ] **`docker-compose.yml`**: Update volumes to map `backend/src:/app/src` (or similar) and check command paths.\n*   [ ] **`backend/alembic.ini`**:\n    *   Update `script_location` to `src/app/adapters/alembic_scripts`.\n    *   Ensure `sqlalchemy.url` can be configured correctly, possibly by reading from `app.config`.\n*   [ ] **`backend/scripts/*.sh`**: Update any paths in these shell scripts.\n*   [ ] **`backend/app/tests_pre_start.py`**: Determine its new role/location.

### 5. Testing

*   [ ] **Run Tests**: Execute your test suite (`pytest backend/tests/`).\n*   [ ] **Fix Failures**: Address any test failures due to path changes, import errors, or refactoring.\n*   [ ] **Test Discovery**: Ensure pytest correctly discovers tests in `backend/tests/`. Update `backend/tests/conftest.py` if needed.

### 6. Review and Refine

*   [ ] **Code Review**: Review the changes against Cosmic Python principles.\n*   [ ] **Clean Up**: Remove any old, now-empty directories (like the original `backend/app/` after moving everything).\n*   [ ] **Documentation**: Update `backend/README.md` to reflect the new structure and how to run/develop the application.

## Phase 2: Iterative Refinement (Post-Move)

Once the basic structure is in place and tests are passing:

*   [ ] **Refactor `crud.py`**: Systematically move logic from `crud.py` into appropriate repositories in `app.adapters.repository` and services in `app.service_layer.services`.\n*   [ ] **Refactor `models.py`**: Further separate domain concepts from persistence details. SQLModel entities can live in `app.adapters.orm.py` or a dedicated `app.adapters.models.py`, while `app.domain.models.py` holds plain Pydantic models or dataclasses representing the core business entities.\n*   [ ] **Refactor `core/db.py` and `core/security.py`**:\n    *   `db.py`\'s engine and session management should be part of `app.adapters.orm` or a UoW.\n    *   `security.py`\'s functions might belong to the service layer, domain, or be utility functions within `app.entrypoints.api.deps` or a shared `app.utils` module if truly generic.\n*   [ ] **Dependency Injection**: Explicitly inject dependencies (like repositories, UoW) into services and entrypoints.\n*   [ ] **Service Layer Logic**: Ensure the service layer contains the core application logic and orchestrates domain objects and repositories.\n*   [ ] **Entrypoint Responsibilities**: Entrypoints (like FastAPI routes) should be thin, delegating to the service layer for business operations.

---

This is a comprehensive plan. We should tackle it step-by-step.
