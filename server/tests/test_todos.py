"""Happy-path tests for every todo endpoint.

Each test starts with an empty table (see conftest.py) and creates the rows it needs
through the API, then reads them back.
"""

from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_todo(title: str = "Buy milk", description: str | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"title": title}
    if description is not None:
        body["description"] = description
    response = client.post("/api/todos", json=body)
    assert response.status_code == 201
    todo: dict[str, Any] = response.json()
    return todo


def ids(response_body: dict[str, Any]) -> list[str]:
    return [todo["id"] for todo in response_body["todos"]]


# --- create / get ---


def test_create_returns_201_with_defaults() -> None:
    response = client.post("/api/todos", json={"title": "  Buy milk  ", "description": "2 litres"})

    assert response.status_code == 201
    todo = response.json()
    UUID(todo["id"])  # raises if the id is not a valid UUID
    assert todo["title"] == "Buy milk"  # surrounding whitespace is stripped
    assert todo["description"] == "2 litres"
    assert todo["done"] is False
    assert todo["created_at"] is not None
    assert todo["updated_at"] is not None


def test_create_without_description_stores_null() -> None:
    todo = create_todo("No details")

    assert todo["description"] is None


def test_get_returns_the_created_todo() -> None:
    todo = create_todo("Buy milk", "2 litres")

    response = client.get(f"/api/todos/{todo['id']}")

    assert response.status_code == 200
    assert response.json() == todo


# --- list ---


def test_list_is_empty_when_there_are_no_todos() -> None:
    response = client.get("/api/todos")

    assert response.status_code == 200
    assert response.json() == {"todos": [], "total": 0, "limit": 20, "offset": 0}


def test_list_returns_newest_first_by_default() -> None:
    first = create_todo("First")
    second = create_todo("Second")

    response = client.get("/api/todos")

    assert response.status_code == 200
    assert ids(response.json()) == [second["id"], first["id"]]


def test_list_filters_by_done() -> None:
    open_todo = create_todo("Still open")
    finished = create_todo("Finished")
    client.patch(f"/api/todos/{finished['id']}/done")

    done_response = client.get("/api/todos", params={"done": "true"})
    open_response = client.get("/api/todos", params={"done": "false"})

    assert ids(done_response.json()) == [finished["id"]]
    assert ids(open_response.json()) == [open_todo["id"]]


# --- pagination and sorting ---


def test_list_pages_with_limit_and_offset() -> None:
    created = [create_todo(f"Todo {n}")["id"] for n in range(5)]
    created.reverse()  # the list is newest first by default

    first_page = client.get("/api/todos", params={"limit": 2, "offset": 0}).json()
    last_page = client.get("/api/todos", params={"limit": 2, "offset": 4}).json()

    assert ids(first_page) == created[:2]
    assert first_page["total"] == 5
    assert first_page["limit"] == 2
    assert ids(last_page) == created[4:]
    assert last_page["offset"] == 4


def test_list_total_counts_filtered_todos_not_the_page() -> None:
    for n in range(3):
        create_todo(f"Open {n}")
    finished = create_todo("Finished")
    client.patch(f"/api/todos/{finished['id']}/done")

    body = client.get("/api/todos", params={"done": "false", "limit": 1}).json()

    assert len(body["todos"]) == 1
    assert body["total"] == 3


def test_list_offset_past_the_end_returns_empty_page() -> None:
    create_todo()

    body = client.get("/api/todos", params={"offset": 10}).json()

    assert body["todos"] == []
    assert body["total"] == 1


def test_list_sorts_by_title_descending() -> None:
    banana = create_todo("Banana")
    apple = create_todo("Apple")
    cherry = create_todo("Cherry")

    body = client.get("/api/todos", params={"sort": "title", "order": "desc"}).json()

    assert ids(body) == [cherry["id"], banana["id"], apple["id"]]


def test_list_sorts_oldest_first_when_asked() -> None:
    first = create_todo("First")
    second = create_todo("Second")

    body = client.get("/api/todos", params={"order": "asc"}).json()

    assert ids(body) == [first["id"], second["id"]]


# --- update ---


def test_update_changes_only_the_fields_sent() -> None:
    todo = create_todo("Old title", "Keep me")

    response = client.put(f"/api/todos/{todo['id']}", json={"title": "New title"})

    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "New title"
    assert updated["description"] == "Keep me"
    assert updated["done"] is False
    assert updated["created_at"] == todo["created_at"]
    assert updated["updated_at"] != todo["updated_at"]
    assert client.get(f"/api/todos/{todo['id']}").json() == updated


def test_update_description_only_keeps_title() -> None:
    todo = create_todo("Title stays", "Old notes")

    response = client.put(f"/api/todos/{todo['id']}", json={"description": "New notes"})

    assert response.status_code == 200
    assert response.json()["title"] == "Title stays"
    assert response.json()["description"] == "New notes"


def test_update_with_empty_body_returns_422() -> None:
    todo = create_todo()

    response = client.put(f"/api/todos/{todo['id']}", json={})

    assert response.status_code == 422
    assert response.json() == {"detail": "Provide at least one of title or description"}


def test_update_missing_todo_returns_404() -> None:
    response = client.put(f"/api/todos/{uuid4()}", json={"title": "Nobody home"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}


# --- toggle ---


def test_toggle_flips_done_and_back() -> None:
    todo = create_todo()

    first = client.patch(f"/api/todos/{todo['id']}/done")
    second = client.patch(f"/api/todos/{todo['id']}/done")

    assert first.status_code == 200
    assert first.json()["done"] is True
    assert second.status_code == 200
    assert second.json()["done"] is False


def test_toggle_missing_todo_returns_404() -> None:
    response = client.patch(f"/api/todos/{uuid4()}/done")

    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}


# --- delete ---


def test_delete_returns_204_and_removes_the_todo() -> None:
    todo = create_todo()

    response = client.delete(f"/api/todos/{todo['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/todos/{todo['id']}").status_code == 404


def test_delete_missing_todo_returns_404() -> None:
    response = client.delete(f"/api/todos/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}
