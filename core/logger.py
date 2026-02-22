from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

_RESET = "\x1b[0m"
_COLORS = {
    "DEBUG": "\x1b[36m",
    "INFO": "\x1b[32m",
    "WARNING": "\x1b[33m",
    "ERROR": "\x1b[31m",
}


class _ColorFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        dt = datetime.fromtimestamp(record.created)
        return dt.strftime("%Y-%m-%d %H:%M:%S") + f".{int(record.msecs):03d}"

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record)
        level = record.levelname
        color = _COLORS.get(level, "")
        pathname = record.pathname
        try:
            pathname = os.path.relpath(pathname)
        except ValueError:
            pass
        message = record.getMessage()
        ctx = getattr(record, "ctx", None)
        ctx_segment = f" | ctx={ctx}" if ctx else ""
        return f"{timestamp} | {color}{level}{_RESET} | {pathname}:{record.lineno} | {message}{ctx_segment}"


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if getattr(root, "_colors_logger_configured", False):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(_ColorFormatter())
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root._colors_logger_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def with_ctx(**kwargs: Any) -> dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None}
