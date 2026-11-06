# Todo List

[![Tests](https://github.com/Schizo00/todo.list/actions/workflows/tests.yml/badge.svg)](https://github.com/Schizo00/todo.list/actions/workflows/tests.yml)

A REST API for managing todos, built with FastAPI and PostgreSQL.

## Quick start

You need Docker.

```bash
docker compose up --build
```

Then open http://localhost:8000/docs to try every endpoint from the browser.

## Repository layout

| Path | Contents |
|---|---|
| [server/](server/) | Python backend: API, database access and tests. **Start with its README.** |
| [client/](client/) | Placeholder for an optional frontend (not built). |
| [docker-compose.yml](docker-compose.yml) | `db` (PostgreSQL), `server` (the API) and `test-db` (a throwaway database for the tests). |
| [.github/workflows/](.github/workflows/) | CI: runs the test suite on every push and pull request. |

## Stack

Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL 17, Poetry, pytest, Docker Compose and GitHub Actions.

See [server/README.md](server/README.md) for local development, the API reference, configuration, tests, and assumptions and limitations.
