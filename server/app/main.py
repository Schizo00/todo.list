from fastapi import FastAPI

from app import endpoints

app = FastAPI(title="Todo List API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/api/todos")
def list_todos():
    return endpoints.list_todos()