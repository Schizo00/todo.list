import pytest

from app.config import Settings


@pytest.mark.parametrize(
    "given",
    [
        "postgres://todo:pw@host:5432/todo",
        "postgresql://todo:pw@host:5432/todo",
        "postgresql+psycopg://todo:pw@host:5432/todo",
    ],
)
def test_database_url_always_uses_psycopg_driver(given: str) -> None:
    settings = Settings(database_url=given)

    assert settings.database_url == "postgresql+psycopg://todo:pw@host:5432/todo"
