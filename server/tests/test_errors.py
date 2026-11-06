from uuid import uuid4

import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app, raise_server_exceptions=False)


def assert_error_shape(response, status_code: int) -> str:
    assert response.status_code == status_code
    body = response.json()
    assert list(body) == ["detail"]
    assert isinstance(body["detail"], str)
    return body["detail"]


def test_missing_todo_returns_404() -> None:
    response = client.get(f"/api/todos/{uuid4()}")

    assert assert_error_shape(response, 404) == "Todo not found"


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ({}, "title: Field required"),
        ({"title": "   "}, "title: Title must not be empty or whitespace"),
        ({"title": "x" * 201}, "title: String should have at most 200 characters"),
        ({"title": "ok", "description": 5}, "description: Input should be a valid string"),
        ({"title": "ok", "done": True}, "done: Extra inputs are not permitted"),
    ],
)
def test_invalid_body_returns_422_with_message(body: dict, expected: str) -> None:
    response = client.post("/api/todos", json=body)

    assert assert_error_shape(response, 422) == expected


def test_malformed_json_returns_422() -> None:
    response = client.post("/api/todos", content=b"{nope", headers={"content-type": "application/json"})

    assert "JSON decode error" in assert_error_shape(response, 422)


def test_invalid_todo_id_returns_422() -> None:
    response = client.get("/api/todos/not-a-uuid")

    assert assert_error_shape(response, 422).startswith("todo_id: Input should be a valid UUID")


def test_unhandled_error_returns_500_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_):
        raise RuntimeError("database exploded")

    monkeypatch.setattr("app.endpoints.list_todos", boom)
    response = client.get("/api/todos")

    assert assert_error_shape(response, 500) == "Internal server error"
