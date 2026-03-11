"""Structured JSON logging for the Sinai API.

Usage:
    from src.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("lead_created", extra={"lead_id": 42, "agency_id": "acme"})

Governance rules (data-governance.md section 9):
- Log event types, IDs, status changes, errors with tracebacks.
- NEVER log: phone numbers, email addresses, raw message bodies.
- Reference message IDs, not content.
"""

import json
import logging
import sys
from datetime import datetime, timezone

# Standard LogRecord keys to exclude from the "extra" JSON block.
_STDLIB_KEYS: frozenset[str] = frozenset({
    "args", "created", "exc_info", "exc_text", "filename", "funcName",
    "levelname", "levelno", "lineno", "message", "module", "msecs", "msg",
    "name", "pathname", "process", "processName", "relativeCreated",
    "stack_info", "taskName", "thread", "threadName",
})

_configured: bool = False


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        extra: dict = {
            key: val
            for key, val in record.__dict__.items()
            if key not in _STDLIB_KEYS and not key.startswith("_")
        }

        if record.exc_info:
            extra["traceback"] = self.formatException(record.exc_info)

        if extra:
            log_obj["extra"] = extra

        return json.dumps(log_obj)


def _configure_root_logging() -> None:
    """Configure the root logger with JSON output exactly once per process."""
    global _configured
    if _configured:
        return

    # Import here to avoid circular imports during early startup.
    from src.core.config import get_settings

    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger backed by the JSON formatter.

    Configures root logging on the first call; subsequent calls are cheap.
    """
    _configure_root_logging()
    return logging.getLogger(name)
