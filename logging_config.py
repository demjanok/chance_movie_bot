"""
Logging configuration module for Chance Movie Bot.

Provides production-ready structured logging (JSON and human-readable text formats)
following industry best practices (12-Factor App, Observability, ELK / Datadog / Loki compatibility).
"""

import datetime
import json
import logging
from pathlib import Path
import sys
import traceback
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

# Ensure standard output streams support UTF-8 on Windows environments
for _stream in (sys.stdout, sys.stderr):
    if _stream and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs single-line JSON records (NDJSON).

    Captures standard log metadata (UTC ISO 8601 timestamp, log level, service name,
    logger name, code location) along with structured exceptions and any extra contextual
    fields passed via `logger.info("...", extra={...})`.
    """

    # Attributes internal to logging.LogRecord that should not be merged as extra fields
    RESERVED_ATTRS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }

    def __init__(self, service_name: str = "chance_movie_bot"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        # Standard structured fields
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.datetime.fromtimestamp(
                record.created, tz=datetime.timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception details when available
        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            log_entry["exception"] = {
                "type": exc_type.__name__ if exc_type else "Exception",
                "message": str(exc_value) if exc_value else "",
                "traceback": traceback.format_exception(*record.exc_info),
            }
        elif record.exc_text:
            log_entry["exception"] = {"traceback": record.exc_text}

        if record.stack_info:
            log_entry["stack_info"] = self.formatStack(record.stack_info)

        # Merge custom contextual attributes passed in `extra={...}`
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and not key.startswith("_"):
                log_entry[key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    third_party_level: Optional[str] = None,
    service_name: str = "chance_movie_bot",
) -> None:
    """
    Configures the root logger with the specified level, format, and handlers.

    :param log_level: Minimum logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
    :param log_format: Output format ('json' for machine-readable JSON, 'text' for console).
    :param log_file: Optional file path for rotating log file. If omitted, logs only to stdout.
    :param third_party_level: Level for chatty libraries (httpx, telegram, etc.).
                              Defaults to WARNING, or DEBUG if log_level is DEBUG.
    :param service_name: Identifier for the application service in structured logs.
    """
    resolved_level = getattr(logging, log_level.upper(), logging.INFO)

    # Determine formatter based on log_format
    if log_format.lower() == "json":
        formatter: logging.Formatter = JSONFormatter(service_name=service_name)
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Prepare handlers
    handlers: list[logging.Handler] = []

    # 1. Stdout handler (12-Factor App event stream)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    stdout_handler.setLevel(resolved_level)
    handlers.append(stdout_handler)

    # 2. Optional Rotating File Handler (10MB per file, up to 5 backups)
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=str(file_path),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(resolved_level)
        handlers.append(file_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(resolved_level)
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)

    # Quiet chatty third-party loggers to keep output clean and signal-to-noise high
    if third_party_level is None:
        tp_level = logging.DEBUG if resolved_level == logging.DEBUG else logging.WARNING
    else:
        tp_level = getattr(logging, third_party_level.upper(), logging.WARNING)

    noisy_loggers = [
        "httpx",
        "httpcore",
        "telegram",
        "telegram.ext",
        "apscheduler",
        "asyncio",
        "urllib3",
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(tp_level)

