"""Structured logging with correlation IDs and redaction."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class RedactingFilter(logging.Filter):
    """Redact sensitive values from log messages."""

    SENSITIVE_PATTERNS = [
        "token",
        "secret",
        "password",
        "key",
        "credential",
        "auth",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive fields from the log message."""
        if isinstance(record.msg, dict):
            record.msg = self._redact_dict(record.msg)  # type: ignore[assignment]
        return True

    def _redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact sensitive keys."""
        redacted: dict[str, Any] = {}
        for key, value in data.items():
            if any(pattern in key.lower() for pattern in self.SENSITIVE_PATTERNS):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self._redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [
                    self._redact_dict(v) if isinstance(v, dict) else v  # type: ignore[assignment]
                    for v in value
                ]
            else:
                redacted[key] = value
        return redacted


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "unknown"
        if not hasattr(record, "task_id"):
            record.task_id = "unknown"
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured JSON logging."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    root_logger.addFilter(RedactingFilter())
    root_logger.addFilter(CorrelationIdFilter())


class StructuredLogger:
    """Structured JSON logger with context."""

    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(name)
        self.logger.addFilter(CorrelationIdFilter())

    def _log(self, level: str, message: str, **context: Any) -> None:
        """Emit a structured log entry."""
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level,
            "logger": self.logger.name,
            "message": message,
            **context,
        }
        self.logger.log(getattr(logging, level), json.dumps(entry, default=str))

    def info(self, message: str, **context: Any) -> None:
        self._log("INFO", message, **context)

    def warning(self, message: str, **context: Any) -> None:
        self._log("WARNING", message, **context)

    def error(self, message: str, **context: Any) -> None:
        self._log("ERROR", message, **context)

    def debug(self, message: str, **context: Any) -> None:
        self._log("DEBUG", message, **context)
