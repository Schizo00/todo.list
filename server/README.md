# Server

Python backend for the todo list app.

## Setup

```bash
cd server
poetry install
cp .env.example .env   # then edit DATABASE_URL if your database differs
```

Configuration is read from environment variables. A `.env` file in `server/` is loaded automatically, and real environment variables take precedence over it. The app refuses to start if `DATABASE_URL` is not set.

## Run

```bash
poetry run uvicorn app.main:app --reload --no-access-log
```

`--no-access-log` turns off uvicorn's own request log, since the app already logs each request with its status and duration.

The API is served at http://127.0.0.1:8000, with interactive docs at http://127.0.0.1:8000/docs.

## Tests

```bash
poetry run pytest
```
