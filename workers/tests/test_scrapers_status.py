"""Tests for scraper status, scrape_runs persistence, and ProductModel last_seen."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from services.database import ProductModel, DatabaseService


def test_product_model_hydrates_last_seen():
    """ProductModel must retain last_seen from DB row."""
    row = {
        "id": "prod-1",
        "external_id": "ext-1",
        "name": "Polera Test",
        "store": "zara",
        "price": 19990,
        "currency": "CLP",
        "category": "Poleras",
        "created_at": "2026-07-01T00:00:00Z",
        "last_seen": "2026-07-02T12:00:00Z",
    }
    model = ProductModel(row)
    assert model.last_seen == "2026-07-02T12:00:00Z"
    assert model.name == "Polera Test"
    assert model.store == "zara"


@pytest.mark.anyio
async def test_save_scrape_run_binds_correct_fields():
    """save_scrape_run must prepare and bind all required fields."""
    mock_env = MagicMock()
    mock_stmt = MagicMock()
    mock_stmt.bind = MagicMock(return_value=mock_stmt)
    mock_stmt.run = AsyncMock(return_value=MagicMock(changes=1))
    mock_env.DB.prepare = MagicMock(return_value=mock_stmt)

    db = DatabaseService(mock_env)
    run_data = {
        "store": "zara",
        "started_at": "2026-07-01T00:00:00Z",
        "finished_at": "2026-07-01T00:01:00Z",
        "status": "completed",
        "total_products": 20,
        "upserted_products": 20,
        "stale_deleted": 2,
        "errors": 0,
        "empty_queries": 0,
        "duration_seconds": 60.5,
    }

    run_id = await db.save_scrape_run(run_data)
    assert run_id is not None
    assert mock_env.DB.prepare.called
    assert mock_stmt.bind.called


@pytest.mark.anyio
async def test_get_scrape_status_detects_stale():
    """get_scrape_status must mark store as stale if last_fresh is older than cutoff."""
    mock_env = MagicMock()

    # Empty runs, but 1 store with old last_fresh
    old_time = (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat()
    mock_runs_stmt = MagicMock()
    mock_runs_stmt.all = AsyncMock(return_value={"results": []})

    mock_fresh_stmt = MagicMock()
    mock_fresh_stmt.all = AsyncMock(return_value={"results": [
        {"store": "zara", "last_fresh": old_time, "product_count": 50}
    ]})

    mock_env.DB.prepare = MagicMock(side_effect=[mock_runs_stmt, mock_fresh_stmt])

    db = DatabaseService(mock_env)
    status = await db.get_scrape_status(stale_threshold_hours=5)

    assert "zara" in status["stores"]
    assert status["stores"]["zara"]["is_stale"] is True
    assert status["stores"]["zara"]["product_count"] == 50
