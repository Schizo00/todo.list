from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, read from environment variables and server/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    log_format: Literal["text", "json"] = "text"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        # Hosts such as Render hand out postgres:// or postgresql:// URLs. On its own,
        # SQLAlchemy reads those as "use psycopg2", which isn't installed; we use psycopg 3.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value


# mypy's pydantic plugin knows the values come from the environment; Pylance doesn't.
settings = Settings()  # pyright: ignore[reportCallIssue]
