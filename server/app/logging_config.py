import json
import logging
from datetime import UTC, datetime

TEXT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

# Attributes every LogRecord has. Anything else on a record came from `extra=`.
# color_message is uvicorn's copy of the message with terminal colour codes.
_STANDARD_ATTRS = set(vars(logging.makeLogRecord({}))) | {
    "message",
    "asctime",
    "taskName",
    "color_message",
}


class JsonFormatter(logging.Formatter):
    """Formats each record as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Fields passed with logger.info(..., extra={...}) become top-level keys.
        entry.update({k: v for k, v in vars(record).items() if k not in _STANDARD_ATTRS})
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def configure_logging(log_format: str, level: str) -> None:
    handler = logging.StreamHandler()
    formatter = JsonFormatter() if log_format == "json" else logging.Formatter(TEXT_FORMAT)
    handler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=[handler], force=True)

    # uvicorn installs its own handlers. Send its startup and error logs through ours,
    # so they use the same format. uvicorn.access is left alone: the app logs each
    # request itself, and uvicorn's --no-access-log flag switches that logger off.
    for name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
