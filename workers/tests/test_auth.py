"""Tests for auth service — JWT tokens and password hashing."""
import os
import time
import pytest
from unittest.mock import MagicMock, patch

# Set env before importing auth
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"

from services.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
    get_jwt_secret,
    _b64url_encode,
    _b64url_decode,
)


def _mock_env():
    env = MagicMock()
    env.JWT_SECRET = "test-secret-key-for-testing-only"
    return env


# ── Password hashing ──────────────────────────────────────

def test_hash_and_verify_password():
    pwd = "MySecureP@ss123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True


def test_wrong_password_fails():
    hashed = hash_password("correct-password")
    assert verify_password("wrong-password", hashed) is False


def test_hash_format():
    hashed = hash_password("test")
    parts = hashed.split(":")
    assert len(parts) == 3
    assert parts[0] == "260000"
    assert len(parts[1]) == 32  # 16 bytes hex
    assert len(parts[2]) == 64  # 32 bytes hex


def test_legacy_bcrypt_returns_false():
    # bcrypt hashes start with $2b$
    assert verify_password("test", "$2b$12$fakehash") is False


# ── JWT tokens ────────────────────────────────────────────

def test_create_and_verify_access_token():
    env = _mock_env()
    token = create_access_token("user-123", "test@example.com", env=env)
    data = verify_token(token, expected_type="access", env=env)
    assert data is not None
    assert data.user_id == "user-123"
    assert data.email == "test@example.com"


def test_create_and_verify_refresh_token():
    env = _mock_env()
    token = create_refresh_token("user-456", "refresh@example.com", env=env)
    data = verify_token(token, expected_type="refresh", env=env)
    assert data is not None
    assert data.user_id == "user-456"


def test_wrong_token_type_rejected():
    env = _mock_env()
    token = create_access_token("user-789", "a@b.com", env=env)
    data = verify_token(token, expected_type="refresh", env=env)
    assert data is None


def test_tampered_token_rejected():
    env = _mock_env()
    token = create_access_token("user-100", "c@d.com", env=env)
    # Tamper with the payload
    parts = token.split(".")
    tampered = parts[0] + "." + parts[1] + "X" + "." + parts[2]
    data = verify_token(tampered, env=env)
    assert data is None


def test_non_hs256_alg_rejected():
    """JWT with alg != HS256 should be rejected (OWASP API2:2023)."""
    import base64
    import json

    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({"sub": "evil", "email": "e@e.com", "exp": 9999999999}).encode()).rstrip(b"=").decode()
    fake_token = f"{header}.{payload}."
    data = verify_token(fake_token, env=_mock_env())
    assert data is None


def test_invalid_token_parts():
    assert verify_token("only.two", env=_mock_env()) is None
    assert verify_token("garbage", env=_mock_env()) is None
    assert verify_token("", env=_mock_env()) is None


def test_b64url_roundtrip():
    data = b"hello world 123"
    encoded = _b64url_encode(data)
    decoded = _b64url_decode(encoded)
    assert decoded == data


def test_jwt_secret_cache():
    """Second call should use cached secret."""
    env = _mock_env()
    s1 = get_jwt_secret(env)
    s2 = get_jwt_secret(env)
    assert s1 == s2


# ── Config error propagation ───────────────────────────────

def test_verify_token_raises_when_secret_missing():
    """verify_token should propagate HTTPException when JWT_SECRET is not configured."""
    from fastapi import HTTPException
    import services.auth as auth_mod
    auth_mod._jwt_secret_cache = None
    # Temporarily remove JWT_SECRET from os.environ so os.getenv returns None
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("JWT_SECRET", None)
        with pytest.raises(HTTPException) as exc_info:
            verify_token("x.y.z", env=None)
        assert exc_info.value.status_code == 500
        assert "JWT_SECRET not configured" in exc_info.value.detail


def test_get_jwt_secret_raises_when_no_source():
    """get_jwt_secret should raise HTTPException with no env and no os.getenv."""
    from fastapi import HTTPException
    import services.auth as auth_mod
    auth_mod._jwt_secret_cache = None
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("JWT_SECRET", None)
        with pytest.raises(HTTPException) as exc_info:
            get_jwt_secret(env=None)
        assert exc_info.value.status_code == 500


def test_expired_token_returns_none():
    """Expired tokens should return None, not raise."""
    env = _mock_env()
    from services.auth import create_access_token, verify_token
    from datetime import timedelta
    # Create a token that expired 1 hour ago
    token = create_access_token("user-exp", "exp@example.com",
                                 expires_delta=timedelta(hours=-1), env=env)
    data = verify_token(token, env=env)
    assert data is None
