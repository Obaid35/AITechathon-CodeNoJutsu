"""Structured JSON logging with request_id injection.

Constitution VI: All module entries/exits MUST emit structured JSON logs
with request_id, module, duration_ms, and status.
"""

import contextvars
import time
import uuid
from typing import Any

import structlog

# Context variable holding the current request_id
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


def _add_request_id(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Inject request_id into every log entry."""
    rid = request_id_ctx.get("")
    if rid:
        event_dict["request_id"] = rid
    return event_dict


def setup_logging(debug: bool = False) -> None:
    """Configure structlog for JSON output."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_request_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            10 if debug else 20  # DEBUG=10, INFO=20
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(module: str) -> structlog.BoundLogger:
    """Get a logger bound to a specific module name."""
    return structlog.get_logger(module=module)


def generate_request_id() -> str:
    """Generate a new UUID4 request ID and set it in context."""
    rid = f"req_{uuid.uuid4().hex[:12]}"
    request_id_ctx.set(rid)
    return rid


class TimingContext:
    """Context manager to measure duration_ms of an operation."""

    def __init__(self, logger: structlog.BoundLogger, operation: str) -> None:
        self.logger = logger
        self.operation = operation
        self._start: float = 0.0

    def __enter__(self) -> "TimingContext":
        self._start = time.perf_counter()
        self.logger.info(f"{self.operation}_start")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        duration_ms = round((time.perf_counter() - self._start) * 1000, 2)
        status = "error" if exc_type else "success"
        self.logger.info(
            f"{self.operation}_end",
            duration_ms=duration_ms,
            status=status,
        )
