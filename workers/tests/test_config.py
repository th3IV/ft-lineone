"""Tests for config and database services."""

import pytest
from services.config import (
    VTON_DAILY_LIMIT_FREE,
    LLM_DAILY_LIMIT_FREE,
    VTON_DAILY_LIMIT_PREMIUM,
    LLM_DAILY_LIMIT_PREMIUM,
    MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP,
    MAX_USER_IMAGE_BYTES,
    ALLOWED_IMAGE_MAGIC,
)


def test_usage_limits():
    """Free-tier limits should be defined."""
    assert VTON_DAILY_LIMIT_FREE == 5
    assert LLM_DAILY_LIMIT_FREE == 5
    assert VTON_DAILY_LIMIT_PREMIUM == -1
    assert LLM_DAILY_LIMIT_PREMIUM == -1


def test_scraper_threshold():
    """Scraper cleanup threshold should prevent data loss."""
    assert MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP >= 3


def test_image_constraints():
    """Image constraints should be reasonable."""
    assert MAX_USER_IMAGE_BYTES == 8 * 1024 * 1024  # 8 MB
    assert b'\xff\xd8\xff' in ALLOWED_IMAGE_MAGIC  # JPEG
    assert b'\x89PNG' in ALLOWED_IMAGE_MAGIC  # PNG
    assert b'RIFF' in ALLOWED_IMAGE_MAGIC  # WebP


def test_config_consistency():
    """Config values should be internally consistent."""
    assert VTON_DAILY_LIMIT_FREE > 0
    assert LLM_DAILY_LIMIT_FREE > 0
    assert VTON_DAILY_LIMIT_PREMIUM == -1
    assert LLM_DAILY_LIMIT_PREMIUM == -1
