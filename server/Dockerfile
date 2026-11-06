FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.2.1 \
 && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --only main --no-root --no-interaction

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
