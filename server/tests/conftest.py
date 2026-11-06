"""Point every test at the throwaway test database instead of the dev database.

Start it first with: docker compose up -d --wait test-db
"""

from collections.abc import Iterator

import pytest
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, create_engine, delete, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.tables import TodoRow


class DbTestSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    test_database_url: str


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    url = DbTestSettings().test_database_url  # pyright: ignore[reportCallIssue]
    # Every row is deleted after each test, so refuse anything that isn't a test database.
    database_name = make_url(url).database or ""
    if not database_name.endswith("_test"):
        raise RuntimeError(
            f"TEST_DATABASE_URL must point at a *_test database, got {database_name!r}"
        )

    engine = create_engine(url)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def use_test_database(test_engine: Engine) -> Iterator[None]:
    TestSession = sessionmaker(bind=test_engine, expire_on_commit=False)

    def get_test_db() -> Iterator[Session]:
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = get_test_db
    yield
    app.dependency_overrides.clear()
    # Empty the table so the next test starts from nothing.
    with TestSession.begin() as session:
        session.execute(delete(TodoRow))
