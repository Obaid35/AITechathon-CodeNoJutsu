"""Structured error handling for NaqsKAR API.

Constitution VI: All errors MUST return JSON with error_code, message, details.
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    """Single field-level error detail."""

    field: Optional[str] = None
    message: str
    type: Optional[str] = None


class ErrorResponse(BaseModel):
    """Structured error response returned by all error handlers."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "1.0",
                    "error_code": "VALIDATION_ERROR",
                    "message": "Request body validation failed",
                    "details": [
                        {
                            "field": "text",
                            "message": "String should have at least 3 characters",
                            "type": "string_too_short",
                        }
                    ],
                }
            ]
        }
    )

    schema_version: str = "1.0"
    error_code: str
    message: str
    details: list[ErrorDetail] = []


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class NaqsKARException(Exception):
    """Base exception for all NaqsKAR errors."""

    def __init__(
        self,
        error_code: str,
        message: str,
        details: list[dict[str, Any]] | None = None,
        status_code: int = 500,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.details = details or []
        self.status_code = status_code
        super().__init__(message)

    def to_response(self) -> ErrorResponse:
        return ErrorResponse(
            error_code=self.error_code,
            message=self.message,
            details=[ErrorDetail(**d) for d in self.details],
        )


class ValidationError(NaqsKARException):
    """Raised when request validation fails beyond Pydantic defaults."""

    def __init__(self, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
            status_code=422,
        )


class ProviderUnavailableError(NaqsKARException):
    """Raised when all ML/LLM providers are unreachable."""

    def __init__(self, message: str, details: list[dict[str, Any]] | None = None):
        super().__init__(
            error_code="LLM_PROVIDER_UNAVAILABLE",
            message=message,
            details=details,
            status_code=503,
        )


class ModuleError(NaqsKARException):
    """Raised when an individual module fails."""

    def __init__(self, module: str, message: str):
        super().__init__(
            error_code=f"MODULE_ERROR_{module.upper()}",
            message=message,
            status_code=500,
        )
