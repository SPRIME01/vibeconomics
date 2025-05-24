from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete  # This is SQLModel's Session, not SQLAlchemy's

from app.config import settings
from app.adapters.orm import engine, init_db  # Updated: orm -> core.db
from app.entrypoints.fastapi_app import app  # Assuming app.main still holds the FastAPI app for now
from app.adapters.orm import Item, User  # Updated: orm -> models
from tests.utils.user import authentication_token_from_email # Corrected path
from tests.utils.utils import get_superuser_token_headers # Corrected path


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
