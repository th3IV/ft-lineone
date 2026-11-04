"""Tests for Default.scheduled handler (Cloudflare Cron Triggers)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from entry import Default


@pytest.mark.anyio
async def test_scheduled_enqueues_active_stores_on_scraper_cron():
    """Scraper cron trigger must enqueue active stores (zara, maui, falabella, hm, fashionpark)."""
    mock_queue = MagicMock()
    mock_queue.send = AsyncMock(return_value=None)

    mock_env = MagicMock()
    mock_env.SCRAPER_QUEUE = mock_queue

    controller = MagicMock()
    controller.cron = "*/5 * * * *"

    entrypoint = Default(mock_env)
    await entrypoint.scheduled(controller, mock_env, None)

    assert mock_queue.send.call_count == 5
    sent_stores = [call.args[0]["store"] for call in mock_queue.send.call_args_list]
    assert sent_stores == ["zara", "maui", "falabella", "hm", "fashionpark"]


@pytest.mark.anyio
async def test_scheduled_invokes_vton_on_vton_cron():
    """VTON cron trigger must invoke process_pending_vton_tasks."""
    mock_env = MagicMock()
    controller = MagicMock()
    controller.cron = "*/2 * * * *"

    entrypoint = Default(mock_env)
    with patch("cron.process_pending_vton_tasks", new=AsyncMock(return_value={"processed": 1})) as mock_vton:
        await entrypoint.scheduled(controller, mock_env, None)
        assert mock_vton.called
        assert mock_vton.call_args[0][0] == mock_env
