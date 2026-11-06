# Server

REST API for the todo list, built with FastAPI, SQLAlchemy 2 and PostgreSQL.

## Quick start (Docker)

From the repo root:

```bash
docker compose up --build
```

This starts PostgreSQL and the API. The API is at http://localhost:8000, with interactive docs at http://localhost:8000/docs. Data is kept in the `pgdata` volume between restarts. `docker compose down -v` deletes it.

## Local development

You need Python 3.13, [Poetry](https://python-poetry.org/) 2.x and Docker (for the database).

```bash
docker compose up -d --wait db   # from the repo root: start PostgreSQL only

cd server
poetry install                   # creates server/.venv
cp .env.example .env             # then edit DATABASE_URL if your database differs
poetry run uvicorn app.main:app --reload --no-access-log
```

`--no-access-log` turns off uvicorn's own request log, since the app already logs each request with its status and duration.

In VS Code, the **API (dev)** launch configuration starts the database and runs the server under the debugger.

### Configuration

Configuration is read from environment variables. A `.env` file in `server/` is loaded automatically, and real environment variables take precedence over it. Commands that read `.env` must be run from `server/`.

| Variable | Used by | Example |
|---|---|---|
| `DATABASE_URL` | the app (required) | `postgresql+psycopg://todo:todo@localhost:5432/todo` |
| `LOG_FORMAT` | the app | `text` (default) or `json` |
| `LOG_LEVEL` | the app | `DEBUG`, `INFO` (default), `WARNING` or `ERROR` |
| `TEST_DATABASE_URL` | the test suite only | `postgresql+psycopg://todo:todo@localhost:5433/todo_test` |

The app refuses to start if `DATABASE_URL` is not set, or if `LOG_FORMAT` or `LOG_LEVEL` has an unknown value.

### Logging

Every request is logged once, with its method, path, status and duration. Errors that return 500 are logged with their stack trace.

With `LOG_FORMAT=text` (the default for local development), logs are readable lines:

```
2026-11-06 16:09:04,640 INFO app.main: GET /api/todos -> 200 (6.4 ms)
```

With `LOG_FORMAT=json` (set in `docker-compose.yml`), each log is one JSON object, so a log collector can filter and search by field:

```json
{"time": "2026-11-06T16:09:04.640723+00:00", "level": "INFO", "logger": "app.main", "message": "GET /api/todos -> 200 (6.4 ms)", "method": "GET", "path": "/api/todos", "status_code": 200, "duration_ms": 6.4}
```

uvicorn's own startup and shutdown messages use the same format.

## API

| Method | Path | Success | Description |
|---|---|---|---|
| `GET` | `/api/todos` | 200 | List todos, one page at a time. See [Listing](#listing). |
| `GET` | `/api/todos/{id}` | 200 | Get one todo. |
| `POST` | `/api/todos` | 201 | Create a todo from `{"title": ..., "description": ...}`. |
| `PUT` | `/api/todos/{id}` | 200 | Update the title and/or description. |
| `PATCH` | `/api/todos/{id}/done` | 200 | Flip `done` between `true` and `false`. No body. |
| `DELETE` | `/api/todos/{id}` | 204 | Delete a todo. |
| `GET` | `/health` | 200 | Liveness check. |

A todo looks like this:

```json
{
  "id": "6f1c1b9e-3c43-4a3e-9a51-2a7d1f0c8e11",
  "title": "Buy milk",
  "description": "2 litres",
  "done": false,
  "created_at": "2026-11-06T10:00:00Z",
  "updated_at": "2026-11-06T10:00:00Z"
}
```

### Listing

`GET /api/todos` takes these optional query parameters:

| Parameter | Default | Allowed values |
|---|---|---|
| `done` | none (all todos) | `true` or `false` |
| `limit` | `20` | 1 to 100 |
| `offset` | `0` | 0 or more |
| `sort` | `created_at` | `created_at`, `updated_at`, `title` |
| `order` | `desc` | `asc`, `desc` |

For example, `GET /api/todos?done=false&sort=title&limit=10&offset=10` returns the second page of 10 open todos, sorted by title:

```json
{"todos": [...], "total": 23, "limit": 10, "offset": 10}
```

`total` is the number of todos matching the filter, ignoring `limit` and `offset`, so a client can work out how many pages there are. Rows with the same sort value are ordered by `id`, so pages don't overlap or skip rows.

### Validation

- `title` is required, must not be blank, and is at most 200 characters. Surrounding whitespace is trimmed.
- `description` is optional, at most 1000 characters. An empty string is stored as `null`.
- `done` defaults to `false` and can only be changed through the toggle endpoint.
- Unknown fields are rejected.

### Errors

Every error response has the same shape:

```json
{"detail": "Todo not found"}
```

| Status | When | Example `detail` |
|---|---|---|
| 404 | The todo does not exist | `Todo not found` |
| 422 | Invalid body, malformed JSON, invalid id or query parameter | `title: Title must not be empty or whitespace` |
| 500 | Unexpected server error | `Internal server error` |

For a 500, the full stack trace is written to the server log and never returned to the client.

## Project layout

```
server/
├── app/
│   ├── main.py       # routes, error handlers, request logging
│   ├── model.py      # Pydantic models: request validation and response shapes
│   ├── crud.py       # database operations, including the 404 when a todo is missing
│   ├── tables.py     # SQLAlchemy table definition
│   ├── database.py   # engine and the per-request session dependency
│   ├── config.py     # settings read from environment variables and .env
│   └── logging_config.py # text or JSON log output
└── tests/
    ├── conftest.py   # points every test at the test database and empties it after each test
    ├── test_todos.py # each endpoint's happy path, pagination, sorting, plus 404s
    ├── test_errors.py# error shape: 404, 422 cases, 500 without a stack trace
    ├── test_logging.py # JSON log format
    └── test_health.py
```

Requests go `main.py` → `crud.py` → database. Validation happens in `model.py` before a route runs, so `crud.py` only receives valid data.

## Database

- PostgreSQL 17, accessed through SQLAlchemy 2 with the psycopg 3 driver.
- One table, `todos`. IDs are UUIDv4 and timestamps are UTC. Both are generated in the application rather than by the database.
- Tables are created at startup with `Base.metadata.create_all`. There are no migrations; see [Limitations](#assumptions-and-limitations).
- Each request gets its own session, which is closed when the request finishes.

## Tests

The tests run against a separate, throwaway PostgreSQL database, so they never touch your dev data. From the repo root:

```bash
docker compose up -d --wait test-db   # PostgreSQL on port 5433, kept in memory, no volume
cd server
poetry run pytest
```

- Each test creates the todos it needs through the API and reads them back. It never relies on existing rows.
- After each test, every row is deleted, so the next test starts from an empty table.
- As a safeguard, the suite refuses to run unless the database name in `TEST_DATABASE_URL` ends in `_test`.

In VS Code, the **Tests** launch configuration starts `test-db` first.

## Linting, formatting and type checking

[Ruff](https://docs.astral.sh/ruff/) lints and formats the code (100-character lines; pycodestyle, pyflakes, import order, bugbear and pyupgrade rules). [mypy](https://mypy.readthedocs.io/) checks types in strict mode, with the Pydantic plugin. Both are configured in `pyproject.toml`. From `server/`:

```bash
poetry run ruff check .          # lint; add --fix to apply safe fixes
poetry run ruff format .         # reformat
poetry run mypy app tests        # type check
```

## Continuous integration

[`.github/workflows/tests.yml`](../.github/workflows/tests.yml) runs on every push and pull request. It runs `ruff check`, `ruff format --check` and `mypy`, then the test suite against a PostgreSQL service container. It reads `DATABASE_URL` and `TEST_DATABASE_URL` from the repository's Actions variables.

## Assumptions and limitations

- **No migrations.** The schema is created with `create_all`, which creates missing tables but never changes existing ones. A schema change needs a manual `ALTER TABLE`, or a reset with `docker compose down -v`. Alembic would be the next step for a real deployment.
- **`PUT` is a partial update.** Only the fields sent are changed. At least one of `title` or `description` is required, `title` cannot be `null`, and sending `"description": null` clears it.
- **Toggle is not idempotent.** Calling it twice returns the todo to its original state. It reads and then writes, so two simultaneous toggles on the same todo could both read the same value.
- **Validation errors are 422**, FastAPI's default, rather than 400.
- **`?done=`** accepts `true`/`false`, as well as `1`/`0`, `yes`/`no` and `on`/`off`. Any other value, including an empty one, returns 422.
- **The title length limit is checked before trimming**, so a title padded with spaces past 200 characters is rejected.
- **Pagination is offset-based.** It's simple, and fine at this scale, but a todo created or deleted between two requests shifts later pages by one. Cursor-based pagination would avoid that.
- **The list returns 20 todos by default.** Clients that want everything must page through it, or pass `limit=100`.
- **Sorting by `title`** uses the database's collation, so the order of upper- and lower-case letters depends on PostgreSQL's locale.
- **No authentication.** Every client sees and edits the same todos.
- **Logs go to standard output only.** Collecting and storing them is left to the platform (Docker, a log shipper). There are no request IDs to tie together the log lines from a single request.
