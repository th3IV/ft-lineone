"""Tests for LLM prompt building."""
import os
import json
import pytest
from unittest.mock import MagicMock

os.environ["JWT_SECRET"] = "test-secret"

from services.llm import LLMService, RECOMMENDATION_SYSTEM_PROMPT


def _mock_env():
    env = MagicMock()
    env.AI = MagicMock()
    return env


def test_prompt_includes_occasions():
    svc = LLMService(_mock_env())
    prefs = {"occasions": ["oficina", "paseo"]}
    products = [{"id": "1", "name": "Test", "store": "test", "price": 10000, "category": "test", "colors": []}]
    prompt = svc._build_recommendation_prompt(prefs, products)
    assert "oficina" in prompt
    assert "paseo" in prompt


def test_prompt_includes_styles():
    svc = LLMService(_mock_env())
    prefs = {"styles": ["minimalista", "streetwear"]}
    products = [{"id": "1", "name": "Test", "store": "test", "price": 10000, "category": "test", "colors": []}]
    prompt = svc._build_recommendation_prompt(prefs, products)
    assert "minimalista" in prompt
    assert "streetwear" in prompt


def test_prompt_includes_avoided_colors():
    svc = LLMService(_mock_env())
    prefs = {"avoided_colors": ["rosa", "verde"]}
    products = [{"id": "1", "name": "Test", "store": "test", "price": 10000, "category": "test", "colors": []}]
    prompt = svc._build_recommendation_prompt(prefs, products)
    assert "rosa" in prompt
    assert "NO quiere usar" in prompt


def test_prompt_includes_favorite_colors():
    svc = LLMService(_mock_env())
    prefs = {"colors": ["negro", "azul"]}
    products = [{"id": "1", "name": "Test", "store": "test", "price": 10000, "category": "test", "colors": []}]
    prompt = svc._build_recommendation_prompt(prefs, products)
    assert "negro" in prompt
    assert "azul" in prompt


def test_prompt_includes_query():
    svc = LLMService(_mock_env())
    prefs = {}
    products = [{"id": "1", "name": "Test", "store": "test", "price": 10000, "category": "test", "colors": []}]
    prompt = svc._build_recommendation_prompt(prefs, products, query="necesito algo formal")
    assert "necesito algo formal" in prompt


def test_system_prompt_mentions_avoided_colors():
    lower = RECOMMENDATION_SYSTEM_PROMPT.lower()
    assert "colores que el usuario" in lower and "no quiere" in lower


def test_prompt_respects_sample_size():
    svc = LLMService(_mock_env())
    prefs = {}
    products = [{"id": str(i), "name": f"Item {i}", "store": "test", "price": 10000, "category": "test", "colors": []} for i in range(50)]
    prompt = svc._build_recommendation_prompt(prefs, products)
    # Should only include up to 20 products
    count = prompt.count('"id"')
    assert count <= 20
