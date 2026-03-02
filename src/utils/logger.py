"""
Agentic NetOps — Structured Logger
Provides JSON-formatted structured logging for the pipeline.
"""

from __future__ import annotations

import logging
import json
import sys
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """Formats log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields (e.g., ticket number, agent name)
        for key in ("ticket", "agent", "status", "error", "device", "action"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        return json.dumps(log_entry)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create a structured logger.

    Args:
        name: Logger name (typically __name__).
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(level)

    return logger
