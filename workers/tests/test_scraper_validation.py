"""Tests for scraper product validation rules."""

import pytest
from unittest.mock import MagicMock
from scrapers.scheduler import ScraperRunner


class DummyProduct:
    def __init__(self, **kwargs):
        self.external_id = kwargs.get("external_id", "ext-123")
        self.name = kwargs.get("name", "Polera Casual Algodón")
        self.price = kwargs.get("price", 19990.0)
        self.currency = kwargs.get("currency", "CLP")
        self.sizes = kwargs.get("sizes", ["S", "M", "L"])
        self.colors = kwargs.get("colors", ["Negro", "Azul"])
        self.image_url = kwargs.get("image_url", "https://example.com/img.jpg")
        self.original_url = kwargs.get("original_url", "https://example.com/item")


def test_valid_product_passes_validation():
    runner = ScraperRunner(MagicMock())
    p = DummyProduct()
    assert runner._validate_product(p) is True


def test_missing_or_empty_external_id_rejected():
    runner = ScraperRunner(MagicMock())
    p1 = DummyProduct(external_id="")
    p2 = DummyProduct(external_id="   ")
    assert runner._validate_product(p1) is False
    assert runner._validate_product(p2) is False


def test_price_range_validation():
    runner = ScraperRunner(MagicMock())
    p_zero = DummyProduct(price=0)
    p_negative = DummyProduct(price=-100)
    p_excessive = DummyProduct(price=6_000_000)
    p_valid = DummyProduct(price=49990)

    assert runner._validate_product(p_zero) is False
    assert runner._validate_product(p_negative) is False
    assert runner._validate_product(p_excessive) is False
    assert runner._validate_product(p_valid) is True


def test_short_name_rejected():
    runner = ScraperRunner(MagicMock())
    p = DummyProduct(name="ab")
    assert runner._validate_product(p) is False


def test_corrupted_colors_or_sizes_rejected():
    runner = ScraperRunner(MagicMock())
    p_corrupted_size = DummyProduct(name="Polera Vintage", sizes=["Polera Vintage"])
    p_corrupted_color = DummyProduct(name="Chaqueta Cuero", colors=["Chaqueta Cuero"])

    assert runner._validate_product(p_corrupted_size) is False
    assert runner._validate_product(p_corrupted_color) is False
