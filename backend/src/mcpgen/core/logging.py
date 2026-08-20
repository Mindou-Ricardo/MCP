"""Logs structurés (JSON) pour le backend."""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Mapping
from typing import Any


class JsonFormatter(logging.Formatter):
    """Formatteur produisant des logs JSON sur une ligne."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, Mapping):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure le logging racine en JSON vers stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())


def get_logger(name: str) -> logging.Logger:
    """Logger nommé prêt à l'emploi."""
    return logging.getLogger(name)
