import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud
from app.config import settings
from app.database import Base, engine, get_db
from app.logging_config import configure_logging
from app.model import Todo, TodoCreate, TodoListParams, TodoPage, TodoUpdate

configure_logging(settings.log_format, settings.log_level)
logger = logging.getLogger(__name__)

DbSession = Annotated[Session, Depends(get_db)]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Todo List API", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/todos", status_code=200, response_model=TodoPage)
def list_todos(db: DbSession, params: Annotated[TodoListParams, Query()]) -> TodoPage:
    return crud.list_todos(db, params)


@app.post("/api/todos", status_code=201, response_model=Todo)
def create_todo(db: DbSession, todo_create: TodoCreate) -> Todo:
    return crud.create_todo(db, todo_create)


@app.get("/api/todos/{todo_id}", status_code=200, response_model=Todo)
def get_todo(db: DbSession, todo_id: UUID) -> Todo:
    return crud.get_todo(db, todo_id)


@app.put("/api/todos/{todo_id}", status_code=200, response_model=Todo)
def update_todo(db: DbSession, todo_id: UUID, todo_update: TodoUpdate) -> Todo:
    return crud.update_todo(db, todo_id, todo_update)


@app.patch("/api/todos/{todo_id}/done", status_code=200, response_model=Todo)
def toggle_todo_status(db: DbSession, todo_id: UUID) -> Todo:
    return crud.toggle_todo_status(db, todo_id)


@app.delete("/api/todos/{todo_id}", status_code=204)
def delete_todo(db: DbSession, todo_id: UUID) -> None:
    crud.delete_todo(db, todo_id)


@app.middleware("http")
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            # Separate fields for JSON logs, so requests can be filtered by status, path, etc.
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    messages = []
    for error in exc.errors():
        field = ".".join(
            str(part) for part in error["loc"] if part not in ("body", "path", "query")
        )
        message = error["msg"].removeprefix("Value error, ")
        messages.append(f"{field}: {message}" if field else message)
    detail = "; ".join(messages)
    logger.warning("Invalid request on %s %s: %s", request.method, request.url.path, detail)
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, _: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
