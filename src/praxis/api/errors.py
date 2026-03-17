# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Standardized API error handling and response formatting.

All API errors are represented as PraxisAPIError instances,
which can be serialized to a consistent JSON structure.
Maps Python exceptions to appropriate HTTP status codes.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


def sanitize_error_message(message: str, dev_mode: bool = False) -> str:
    """Sanitize error messages to prevent leaking internal information.

    In dev mode, the full message is returned for debugging.
    In production mode, file paths and SQL fragments are redacted.

    Args:
        message: The raw error message.
        dev_mode: If True, return the message unchanged.

    Returns:
        Sanitized error message safe for external consumption.
    """
    if dev_mode:
        return message
    # Strip file paths (Unix and Windows style)
    message = re.sub(r"[/\\][\w./\\-]+\.py\b", "[internal]", message)
    # Strip SQL statement fragments
    message = re.sub(
        r"\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)\b.*",
        "[query error]",
        message,
        flags=re.IGNORECASE,
    )
    return message


@dataclass
class PraxisAPIError:
    """Standardized API error response.

    Attributes:
        status_code: HTTP status code.
        error_type: Machine-readable error type (e.g., "not_found", "validation_error").
        message: Human-readable error message.
        detail: Optional additional detail dict for debugging.
    """

    status_code: int
    error_type: str
    message: str
    detail: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the error to a response-ready dict.

        Returns:
            Dict with an 'error' key containing type, message,
            and optionally detail.
        """
        error_body: dict[str, Any] = {
            "type": self.error_type,
            "message": self.message,
        }
        if self.detail is not None:
            error_body["detail"] = self.detail
        return {"error": error_body}


# ---------------------------------------------------------------------------
# Factory functions for common error types
# ---------------------------------------------------------------------------


def not_found(resource_type: str, resource_id: str) -> PraxisAPIError:
    """Create a 404 Not Found error.

    Args:
        resource_type: Type of resource (e.g., "Session", "Workspace").
        resource_id: Identifier of the missing resource.

    Returns:
        PraxisAPIError with status_code 404.
    """
    return PraxisAPIError(
        status_code=404,
        error_type="not_found",
        message=f"{resource_type} '{resource_id}' not found",
        detail={"resource_type": resource_type, "resource_id": resource_id},
    )


def validation_error(message: str, detail: dict[str, Any] | None = None) -> PraxisAPIError:
    """Create a 400 Validation Error.

    Args:
        message: Description of what failed validation.
        detail: Optional field-level error details.

    Returns:
        PraxisAPIError with status_code 400.
    """
    return PraxisAPIError(
        status_code=400,
        error_type="validation_error",
        message=message,
        detail=detail,
    )


def conflict_error(message: str) -> PraxisAPIError:
    """Create a 409 Conflict error.

    Args:
        message: Description of the conflict.

    Returns:
        PraxisAPIError with status_code 409.
    """
    return PraxisAPIError(
        status_code=409,
        error_type="conflict",
        message=message,
    )


def forbidden_error(message: str) -> PraxisAPIError:
    """Create a 403 Forbidden error.

    Args:
        message: Description of why access is forbidden.

    Returns:
        PraxisAPIError with status_code 403.
    """
    return PraxisAPIError(
        status_code=403,
        error_type="forbidden",
        message=message,
    )


def internal_error(message: str) -> PraxisAPIError:
    """Create a 500 Internal Server Error.

    Args:
        message: Description of the internal error.

    Returns:
        PraxisAPIError with status_code 500.
    """
    return PraxisAPIError(
        status_code=500,
        error_type="internal_error",
        message=message,
    )


def unauthorized_error(message: str) -> PraxisAPIError:
    """Create a 401 Unauthorized error.

    Args:
        message: Description of why authentication failed.

    Returns:
        PraxisAPIError with status_code 401.
    """
    return PraxisAPIError(
        status_code=401,
        error_type="unauthorized",
        message=message,
    )


# ---------------------------------------------------------------------------
# Exception to error mapping
# ---------------------------------------------------------------------------


def error_from_exception(exc: Exception, dev_mode: bool = False) -> PraxisAPIError:
    """Map a Python exception to a PraxisAPIError.

    Translates known exception types to appropriate HTTP error responses.
    Unknown exceptions become 500 Internal Server Errors.

    In production mode (dev_mode=False), error messages are sanitized to
    prevent leaking internal file paths and SQL fragments.

    Args:
        exc: The exception to map.
        dev_mode: If True, include full error detail in messages.

    Returns:
        PraxisAPIError with the appropriate status code and error type.
    """
    from praxis.api.auth import AuthenticationError
    from praxis.core.session import (
        InvalidStateTransitionError,
        PhaseGateError,
        SessionNotActiveError,
    )

    if isinstance(exc, PhaseGateError):
        return PraxisAPIError(
            status_code=202,
            error_type="phase_gate",
            message=str(exc),
            detail={"held_action_id": exc.held_action_id},
        )
    elif isinstance(exc, AuthenticationError):
        return PraxisAPIError(
            status_code=401,
            error_type="unauthorized",
            message=sanitize_error_message(str(exc), dev_mode=dev_mode),
        )
    elif isinstance(exc, KeyError):
        return PraxisAPIError(
            status_code=404,
            error_type="not_found",
            message=sanitize_error_message(str(exc).strip("'\""), dev_mode=dev_mode),
        )
    elif isinstance(exc, ValueError):
        return PraxisAPIError(
            status_code=400,
            error_type="validation_error",
            message=sanitize_error_message(str(exc), dev_mode=dev_mode),
        )
    elif isinstance(exc, InvalidStateTransitionError):
        return PraxisAPIError(
            status_code=409,
            error_type="conflict",
            message=sanitize_error_message(str(exc), dev_mode=dev_mode),
        )
    elif isinstance(exc, SessionNotActiveError):
        return PraxisAPIError(
            status_code=409,
            error_type="conflict",
            message=sanitize_error_message(str(exc), dev_mode=dev_mode),
        )
    elif isinstance(exc, FileNotFoundError):
        return PraxisAPIError(
            status_code=404,
            error_type="not_found",
            message=sanitize_error_message(str(exc), dev_mode=dev_mode),
        )
    else:
        logger.error("Unhandled exception in API: %s: %s", type(exc).__name__, exc)
        return PraxisAPIError(
            status_code=500,
            error_type="internal_error",
            message="An internal error occurred. Check server logs for details.",
        )
