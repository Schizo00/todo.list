from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, read from environment variables and server/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    log_format: Literal["text", "json"] = "text"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


# mypy's pydantic plugin knows the values come from the environment; Pylance doesn't.
settings = Settings()  # pyright: ignore[reportCallIssue]
