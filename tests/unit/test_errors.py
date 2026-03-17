# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""Unit tests for praxis.api.errors — API error handling and response formatting."""

import pytest


# ---------------------------------------------------------------------------
# PraxisAPIError
# ---------------------------------------------------------------------------


class TestPraxisAPIError:
    """Test the PraxisAPIError class."""

    def test_create_error_with_all_fields(self):
        from praxis.api.errors import PraxisAPIError

        err = PraxisAPIError(
            status_code=404,
            error_type="not_found",
            message="Session not found",
            detail={"session_id": "abc-123"},
        )
        assert err.status_code == 404
        assert err.error_type == "not_found"
        assert err.message == "Session not found"
        assert err.detail == {"session_id": "abc-123"}

    def test_create_error_without_detail(self):
        from praxis.api.errors import PraxisAPIError

        err = PraxisAPIError(
            status_code=500,
            error_type="internal_error",
            message="Something went wrong",
        )
        assert err.detail is None

    def test_error_to_dict(self):
        from praxis.api.errors import PraxisAPIError

        err = PraxisAPIError(
            status_code=400,
            error_type="validation_error",
            message="Invalid input",
            detail={"field": "workspace_id"},
        )
        d = err.to_dict()
        assert d["error"]["type"] == "validation_error"
        assert d["error"]["message"] == "Invalid input"
        assert d["error"]["detail"] == {"field": "workspace_id"}

    def test_error_to_dict_without_detail_omits_detail(self):
        from praxis.api.errors import PraxisAPIError

        err = PraxisAPIError(
            status_code=500,
            error_type="internal_error",
            message="Something went wrong",
        )
        d = err.to_dict()
        assert "detail" not in d["error"]


# ---------------------------------------------------------------------------
# Error factory functions
# ---------------------------------------------------------------------------


class TestErrorFactories:
    """Test convenience factory functions for common error types."""

    def test_not_found_error(self):
        from praxis.api.errors import not_found

        err = not_found("Session", "abc-123")
        assert err.status_code == 404
        assert err.error_type == "not_found"
        assert "Session" in err.message
        assert "abc-123" in err.message

    def test_validation_error(self):
        from praxis.api.errors import validation_error

        err = validation_error("workspace_id must not be empty")
        assert err.status_code == 400
        assert err.error_type == "validation_error"
        assert "workspace_id" in err.message

    def test_conflict_error(self):
        from praxis.api.errors import conflict_error

        err = conflict_error("Session is already archived")
        assert err.status_code == 409
        assert err.error_type == "conflict"

    def test_forbidden_error(self):
        from praxis.api.errors import forbidden_error

        err = forbidden_error("Action blocked by constraints")
        assert err.status_code == 403
        assert err.error_type == "forbidden"

    def test_internal_error(self):
        from praxis.api.errors import internal_error

        err = internal_error("Unexpected failure")
        assert err.status_code == 500
        assert err.error_type == "internal_error"

    def test_unauthorized_error(self):
        from praxis.api.errors import unauthorized_error

        err = unauthorized_error("Invalid token")
        assert err.status_code == 401
        assert err.error_type == "unauthorized"


# ---------------------------------------------------------------------------
# Exception to error mapping
# ---------------------------------------------------------------------------


class TestExceptionMapping:
    """Test mapping Python exceptions to API errors."""

    def test_key_error_maps_to_not_found(self):
        from praxis.api.errors import error_from_exception

        err = error_from_exception(KeyError("Session 'xyz' not found"))
        assert err.status_code == 404
        assert err.error_type == "not_found"

    def test_value_error_maps_to_validation_error(self):
        from praxis.api.errors import error_from_exception

        err = error_from_exception(ValueError("workspace_id must not be empty"))
        assert err.status_code == 400
        assert err.error_type == "validation_error"

    def test_generic_exception_maps_to_internal_error(self):
        from praxis.api.errors import error_from_exception

        err = error_from_exception(RuntimeError("Unexpected"))
        assert err.status_code == 500
        assert err.error_type == "internal_error"

    def test_invalid_state_transition_maps_to_conflict(self):
        from praxis.core.session import InvalidStateTransitionError
        from praxis.api.errors import error_from_exception

        err = error_from_exception(InvalidStateTransitionError("Cannot transition"))
        assert err.status_code == 409
        assert err.error_type == "conflict"

    def test_session_not_active_maps_to_conflict(self):
        from praxis.core.session import SessionNotActiveError
        from praxis.api.errors import error_from_exception

        err = error_from_exception(SessionNotActiveError("Session archived"))
        assert err.status_code == 409
        assert err.error_type == "conflict"


# ---------------------------------------------------------------------------
# Error message sanitization
# ---------------------------------------------------------------------------


class TestSanitizeErrorMessage:
    """Test sanitize_error_message for production safety."""

    def test_dev_mode_returns_full_message(self):
        from praxis.api.errors import sanitize_error_message

        msg = "Error at /usr/local/lib/python3.12/site-packages/praxis/core/session.py"
        assert sanitize_error_message(msg, dev_mode=True) == msg

    def test_strips_unix_file_paths(self):
        from praxis.api.errors import sanitize_error_message

        msg = "Error at /usr/local/lib/python3.12/praxis/core/session.py line 42"
        sanitized = sanitize_error_message(msg, dev_mode=False)
        assert "/usr/local" not in sanitized
        assert "session.py" not in sanitized
        assert "[internal]" in sanitized

    def test_strips_sql_fragments(self):
        from praxis.api.errors import sanitize_error_message

        msg = "Error: SELECT * FROM sessions WHERE id = 'abc-123'"
        sanitized = sanitize_error_message(msg, dev_mode=False)
        assert "SELECT" not in sanitized
        assert "sessions" not in sanitized
        assert "[query error]" in sanitized

    def test_strips_insert_statements(self):
        from praxis.api.errors import sanitize_error_message

        msg = "Failed: INSERT INTO users VALUES ('admin', 'pass')"
        sanitized = sanitize_error_message(msg, dev_mode=False)
        assert "INSERT" not in sanitized
        assert "[query error]" in sanitized

    def test_plain_message_unchanged(self):
        from praxis.api.errors import sanitize_error_message

        msg = "Session not found"
        assert sanitize_error_message(msg, dev_mode=False) == msg

    def test_error_from_exception_sanitizes_in_production(self):
        from praxis.api.errors import error_from_exception

        exc = ValueError("Config error at /etc/praxis/config.py: bad value")
        err = error_from_exception(exc, dev_mode=False)
        assert "/etc/praxis" not in err.message
        assert "[internal]" in err.message

    def test_error_from_exception_preserves_in_dev(self):
        from praxis.api.errors import error_from_exception

        exc = ValueError("Config error at /etc/praxis/config.py: bad value")
        err = error_from_exception(exc, dev_mode=True)
        assert "/etc/praxis" in err.message
