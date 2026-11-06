# Server

Python backend for the todo list app.

## Setup

```bash
cd server
poetry install
```

## Run

```bash
poetry run uvicorn app.main:app --reload
```

The API is served at http://127.0.0.1:8000, with interactive docs at http://127.0.0.1:8000/docs.

## Tests

```bash
poetry run pytest
```
