"""Tests for middleware security helpers."""

from types import SimpleNamespace
from unittest.mock import MagicMock


def _make_request(environment="development"):
    """Create a mock request with app.state.env.ENVIRONMENT."""
    env = SimpleNamespace(ENVIRONMENT=environment)
    request = MagicMock()
    request.app.state.env = env
    return request


def test_safe_error_message_dev_mode():
    """In dev mode, safe_error_message returns the actual exception message."""
    request = _make_request("development")
    from middleware.security import safe_error_message
    result = safe_error_message(Exception("DB connection refused on port 5432"), request)
    assert result == "DB connection refused on port 5432"


def test_safe_error_message_production_mode():
    """In production, safe_error_message returns a generic message."""
    request = _make_request("production")
    from middleware.security import safe_error_message
    result = safe_error_message(Exception("D1 connection pool exhausted"), request)
    assert result == "An internal error occurred. Please try again."
    assert "D1" not in result
    assert "pool" not in result


def test_safe_error_message_empty_env():
    """With no ENVIRONMENT set, defaults to dev behavior."""
    request = _make_request("")
    from middleware.security import safe_error_message
    result = safe_error_message(Exception("secret_key_abc123"), request)
    assert result == "secret_key_abc123"


def test_safe_error_message_none_type_error():
    """safe_error_message handles non-string exceptions gracefully."""
    from middleware.security import safe_error_message
    result = safe_error_message(TypeError(42))
    assert isinstance(result, str)
