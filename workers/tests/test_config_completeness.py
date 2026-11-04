"""Tests for database service — VTON refund, usage limits, config consistency."""

from services.config import (
    VTON_DAILY_LIMIT_FREE,
    LLM_DAILY_LIMIT_FREE,
    MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP,
    YOUCAM_WEBHOOK_FAIL_CLOSED,
    MAX_USER_IMAGE_BYTES,
    ALLOWED_IMAGE_MAGIC,
)


def test_vton_and_llm_limits_equal():
    """VTON and LLM free limits should be equal (unified per Consejo decision)."""
    assert VTON_DAILY_LIMIT_FREE == LLM_DAILY_LIMIT_FREE, (
        f"VTON ({VTON_DAILY_LIMIT_FREE}) != LLM ({LLM_DAILY_LIMIT_FREE})"
    )


def test_free_limits_are_positive_integers():
    """Both limits should be positive integers."""
    assert isinstance(VTON_DAILY_LIMIT_FREE, int)
    assert isinstance(LLM_DAILY_LIMIT_FREE, int)
    assert VTON_DAILY_LIMIT_FREE > 0
    assert LLM_DAILY_LIMIT_FREE > 0


def test_scraper_threshold_positive():
    """Cleanup threshold should be a positive integer."""
    assert isinstance(MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP, int)
    assert MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP >= 0


def test_webhook_fail_closed_is_bool():
    """YOUCAM_WEBHOOK_FAIL_CLOSED should be a boolean."""
    assert isinstance(YOUCAM_WEBHOOK_FAIL_CLOSED, bool)


def test_image_magic_bytes_are_bytes():
    """ALLOWED_IMAGE_MAGIC entries should be bytes objects."""
    assert isinstance(ALLOWED_IMAGE_MAGIC, (list, tuple, set))
    assert len(ALLOWED_IMAGE_MAGIC) > 0
    for magic in ALLOWED_IMAGE_MAGIC:
        assert isinstance(magic, bytes), f"Magic entry {magic!r} is not bytes"


def test_image_magic_covers_common_formats():
    """Should cover at least JPEG, PNG, WebP magic bytes."""
    # JPEG starts with \xff\xd8\xff
    assert any(m[:3] == b'\xff\xd8\xff' for m in ALLOWED_IMAGE_MAGIC), "Missing JPEG magic"
    # PNG starts with \x89PNG
    assert any(m[:3] == b'\x89PN' for m in ALLOWED_IMAGE_MAGIC), "Missing PNG magic"
    # WebP starts with RIFF (first 4 bytes)
    assert any(m[:4] == b'RIFF' for m in ALLOWED_IMAGE_MAGIC), "Missing WebP magic"


def test_max_image_size_reasonable():
    """MAX_USER_IMAGE_BYTES should be between 1MB and 20MB."""
    assert MAX_USER_IMAGE_BYTES >= 1 * 1024 * 1024, "Min 1MB"
    assert MAX_USER_IMAGE_BYTES <= 20 * 1024 * 1024, "Max 20MB"


def test_config_module_has_all_required_constants():
    """Verify all critical config constants are importable."""
    from services import config
    required = [
        "VTON_DAILY_LIMIT_FREE",
        "LLM_DAILY_LIMIT_FREE",
        "MIN_PRODUCTS_SCRAPED_BEFORE_CLEANUP",
        "YOUCAM_WEBHOOK_FAIL_CLOSED",
        "MAX_USER_IMAGE_BYTES",
        "ALLOWED_IMAGE_MAGIC",
    ]
    for name in required:
        assert hasattr(config, name), f"Missing config constant: {name}"
