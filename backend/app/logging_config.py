"""Logging system for the EXO backend.

Configures the root logger with:
- A console handler (human-readable format).
- A rotating file handler (plain text or JSON, controlled by ``EXO_LOG_JSON``).

All application loggers should be obtained via ``logging.getLogger("exo.<area>")``
so records inherit this configuration.
"""

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.config import Settings

_MAX_BYTES = 5 * 1024 * 1024  # 5 MiB per log file
_BACKUP_COUNT = 3
_TEXT_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


class JsonFormatter(logging.Formatter):
    """Serialise log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(settings: Settings) -> None:
    """Configure root logging handlers. Idempotent across repeated calls."""
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    # Clear existing handlers so repeated app factory calls (tests, --reload)
    # do not produce duplicate log lines.
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(_TEXT_FORMAT))
    root.addHandler(console)

    log_dir = Path(settings.log_dir).expanduser().resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "exo.log",
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        JsonFormatter() if settings.log_json else logging.Formatter(_TEXT_FORMAT)
    )
    root.addHandler(file_handler)

    # Reduce noise from access logs; errors still propagate.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
