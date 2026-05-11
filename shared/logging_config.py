import json
import logging
import sys
import uuid
from typing import Optional

from flask import g, request


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter with correlation ID support."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, "service", "unknown"),
        }

        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(service_name: str, level: str = "INFO"):
    """Configure structured JSON logging for a service."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers = [handler]

    # Inject service name into all log records
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        record.correlation_id = _get_correlation_id()
        return record

    logging.setLogRecordFactory(record_factory)


def _get_correlation_id() -> Optional[str]:
    """Get correlation ID from Flask request context if available."""
    try:
        return getattr(g, "correlation_id", None)
    except RuntimeError:
        return None


def correlation_id_middleware(app):
    """Flask middleware that extracts or generates a correlation ID."""

    @app.before_request
    def set_correlation_id():
        g.correlation_id = request.headers.get(
            "X-Correlation-ID", str(uuid.uuid4())
        )

    @app.after_request
    def add_correlation_id_header(response):
        correlation_id = getattr(g, "correlation_id", None)
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id
        return response
