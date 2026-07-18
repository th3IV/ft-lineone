"""Tests for auth routes — password hashing and JWT tokens."""

import pytest
from services.auth import hash_password, verify_password, create_access_token, verify_token


def test_hash_password():
    """Password hashing should produce consistent hashes."""
    hashed = hash_password("test123")
    assert hashed != "test123"
    assert verify_password("test123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_token_creation_and_verification():
    """JWT tokens should be creatable and verifiable."""
    token = create_access_token("user123", "test@example.com")
    payload = verify_token(token)
    assert payload is not None
    assert payload.user_id == "user123"
    assert payload.email == "test@example.com"


def test_invalid_token():
    """Invalid tokens should return None."""
    result = verify_token("invalid.token.here")
    assert result is None


def test_expired_token():
    """Expired tokens should return None."""
    from datetime import timedelta
    token = create_access_token("user123", "test@example.com", expires_delta=timedelta(seconds=-1))
    result = verify_token(token)
    assert result is None
