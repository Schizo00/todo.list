from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app import endpoints, tables  # noqa: F401  (importing tables registers them with Base)
from app.database import Base, engine, get_db
from app.model import TodoCreate, TodoUpdate, Todo

DbSession = Annotated[Session, Depends(get_db)]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Todo List API", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/api/todos")
def list_todos(db: DbSession):
    return endpoints.list_todos(db)

@app.post("/api/todos")
def create_todo(db: DbSession, todo_create: TodoCreate):
    return endpoints.create_todo(db, todo_create)