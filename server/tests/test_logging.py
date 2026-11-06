import json
import logging
import sys

from app.logging_config import JsonFormatter


def make_record(**kwargs: object) -> logging.LogRecord:
    defaults: dict[str, object] = {
        "name": "app.test",
        "levelno": logging.INFO,
        "levelname": "INFO",
        "msg": "Created todo %s",
        "args": ("abc",),
    }
    return logging.makeLogRecord(defaults | kwargs)


def test_json_formatter_outputs_one_json_object() -> None:
    entry = json.loads(JsonFormatter().format(make_record()))

    assert entry["level"] == "INFO"
    assert entry["logger"] == "app.test"
    assert entry["message"] == "Created todo abc"
    assert entry["time"].endswith("+00:00")


def test_json_formatter_includes_extra_fields() -> None:
    record = make_record(status_code=404, path="/api/todos/x")

    entry = json.loads(JsonFormatter().format(record))

    assert entry["status_code"] == 404
    assert entry["path"] == "/api/todos/x"


def test_json_formatter_includes_exception() -> None:
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = make_record(exc_info=sys.exc_info())

    entry = json.loads(JsonFormatter().format(record))

    assert "RuntimeError: boom" in entry["exception"]
