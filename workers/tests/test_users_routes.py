"""Tests for user routes helpers and image constraints."""

import pytest
from services.config import MAX_USER_IMAGE_BYTES, ALLOWED_IMAGE_MAGIC


def test_allowed_image_magic_contains_required_types():
    """ALLOWED_IMAGE_MAGIC must cover JPEG, PNG, and WebP/RIFF."""
    assert b'\xff\xd8\xff' in ALLOWED_IMAGE_MAGIC
    assert b'\x89PNG' in ALLOWED_IMAGE_MAGIC
    assert b'RIFF' in ALLOWED_IMAGE_MAGIC


def test_magic_bytes_detection():
    """Verify detection logic for JPEG, PNG, WebP headers."""
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF'
    png_header = b'\x89PNG\r\n\x1a\n'
    webp_header = b'RIFF\x00\x00\x00\x00WEBP'
    fake_header = b'<svg><script>'

    assert any(jpeg_header[:8].startswith(m) for m in ALLOWED_IMAGE_MAGIC)
    assert any(png_header[:8].startswith(m) for m in ALLOWED_IMAGE_MAGIC)
    assert any(webp_header[:8].startswith(m) for m in ALLOWED_IMAGE_MAGIC)
    assert not any(fake_header[:8].startswith(m) for m in ALLOWED_IMAGE_MAGIC)


def test_max_image_size_is_8mb():
    """User image max limit must be 8MB."""
    assert MAX_USER_IMAGE_BYTES == 8 * 1024 * 1024
