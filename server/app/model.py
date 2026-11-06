from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class TodoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("title")
    @classmethod
    def title_validator(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title must not be empty or whitespace")
        return value.strip()

    @field_validator("description")
    @classmethod
    def description_validator(cls, value: str | None) -> str | None:
        return (value.strip() or None) if value is not None else None


class TodoUpdate(TodoCreate):
    title: str | None = Field(default=None, max_length=200)

    @field_validator("title")
    @classmethod
    def title_validator(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Title must not be null")
        return super().title_validator(value)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "TodoUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one of title or description")
        return self


class TodoListParams(BaseModel):
    """Query parameters for GET /api/todos."""

    done: bool | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort: Literal["created_at", "updated_at", "title"] = "created_at"
    order: Literal["asc", "desc"] = "desc"


class Todo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    done: bool = False
    created_at: datetime
    updated_at: datetime


class TodoPage(BaseModel):
    todos: list[Todo]
    total: int
    limit: int
    offset: int
