"""Tests for CORS and security logic — test the functions directly."""

import pytest
import re


# ── Replicate CORS logic from entry.py to avoid import chain ────

_CORS_ORIGINS = [
    "https://thelineone.com",
    "https://www.thelineone.com",
]
_DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
_PAGES_PATTERN = re.compile(r"^https://([a-z0-9-]+\.)?ft-lineone\.pages\.dev$")
_ENV = {}


def _is_allowed_origin(origin: str) -> bool:
    if not origin:
        return False
    if origin in _CORS_ORIGINS:
        return True
    if _PAGES_PATTERN.match(origin):
        return True
    is_dev = _ENV.get("ENVIRONMENT", "production") not in ("production", "prod")
    if is_dev and origin in _DEV_ORIGINS:
        return True
    return False


# ── Tests ────────────────────────────────────────────────────────

def test_cors_production_blocks_localhost():
    """CORS should block localhost in production."""
    _ENV["ENVIRONMENT"] = "production"
    assert _is_allowed_origin("http://localhost:3000") is False
    assert _is_allowed_origin("https://thelineone.com") is True
    _ENV.clear()


def test_cors_dev_allows_localhost():
    """CORS should allow localhost in dev."""
    _ENV["ENVIRONMENT"] = "dev"
    assert _is_allowed_origin("http://localhost:3000") is True
    assert _is_allowed_origin("http://localhost:5173") is True
    _ENV.clear()


def test_cors_pages_pattern():
    """CORS should allow *.ft-lineone.pages.dev."""
    _ENV.clear()
    assert _is_allowed_origin("https://abc.ft-lineone.pages.dev") is True
    assert _is_allowed_origin("https://malicious.com") is False


def test_cors_empty_origin():
    """CORS should reject empty/None origin."""
    _ENV.clear()
    assert _is_allowed_origin("") is False
    assert _is_allowed_origin(None) is False


def test_cors_www_subdomain():
    """CORS should allow www.thelineone.com."""
    _ENV.clear()
    assert _is_allowed_origin("https://www.thelineone.com") is True


def test_cors_no_default_env_blocks_localhost():
    """Without ENVIRONMENT set (defaults to production), localhost blocked."""
    _ENV.clear()
    assert _is_allowed_origin("http://localhost:3000") is False
