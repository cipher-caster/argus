"""
Tests for the Telegram notifier (app.trading.notifier).

Covers:
- Successful dispatch on WIN / LOSS position-closed outcomes
- Silent no-op when TELEGRAM_BOT_TOKEN is missing
- Silent no-op when TELEGRAM_CHAT_ID is missing
- Graceful handling of httpx errors (never raises)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.trading import notifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_closed_position(outcome="WIN", direction="LONG"):
    pos = MagicMock()
    pos.symbol = "BTCUSDT"
    pos.direction = direction
    pos.outcome = outcome
    pos.pnl_usd = 12.34 if outcome == "WIN" else -8.76
    pos.pnl_pct = 2.5 if outcome == "WIN" else -1.8
    pos.intended_entry = 50000.0
    pos.actual_entry = 50010.0
    pos.actual_exit = 51250.0 if outcome == "WIN" else 49100.0
    pos.intended_tp = 52000.0
    pos.intended_sl = 49000.0
    pos.quote_amount = 100.0
    pos.risk_amount = 10.0
    pos.conviction = 75
    return pos


class FakeAsyncClient:
    """Context-manager stand-in for httpx.AsyncClient that records POST calls."""
    def __init__(self, post_side_effect=None):
        self.post = AsyncMock(side_effect=post_side_effect)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


# ---------------------------------------------------------------------------
# Credentials configured — HTTP dispatch happens
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_notify_position_closed_win_sends_http():
    fake_client = FakeAsyncClient()
    with patch.object(notifier, "_BOT_TOKEN", "test-token"), \
         patch.object(notifier, "_CHAT_ID", "12345"), \
         patch.object(notifier.httpx, "AsyncClient", return_value=fake_client):
        await notifier.notify_position_closed(make_closed_position(outcome="WIN"))

    fake_client.post.assert_awaited_once()
    url, kwargs = fake_client.post.call_args.args[0], fake_client.post.call_args.kwargs
    assert "test-token" in url
    payload = kwargs["json"]
    assert payload["chat_id"] == "12345"
    assert "WIN" in payload["text"]
    assert "BTCUSDT" in payload["text"]


@pytest.mark.asyncio
async def test_notify_position_closed_loss_sends_http():
    fake_client = FakeAsyncClient()
    with patch.object(notifier, "_BOT_TOKEN", "test-token"), \
         patch.object(notifier, "_CHAT_ID", "12345"), \
         patch.object(notifier.httpx, "AsyncClient", return_value=fake_client):
        await notifier.notify_position_closed(make_closed_position(outcome="LOSS"))

    fake_client.post.assert_awaited_once()
    payload = fake_client.post.call_args.kwargs["json"]
    assert "LOSS" in payload["text"]
    assert payload["parse_mode"] == "HTML"


# ---------------------------------------------------------------------------
# Missing credentials — silent no-op
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_op_when_bot_token_missing():
    fake_client = FakeAsyncClient()
    with patch.object(notifier, "_BOT_TOKEN", None), \
         patch.object(notifier, "_CHAT_ID", "12345"), \
         patch.object(notifier.httpx, "AsyncClient", return_value=fake_client) as mock_cls:
        # Should not raise, and should not construct an httpx client
        await notifier.notify_position_closed(make_closed_position(outcome="WIN"))

    mock_cls.assert_not_called()
    fake_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_no_op_when_chat_id_missing():
    fake_client = FakeAsyncClient()
    with patch.object(notifier, "_BOT_TOKEN", "test-token"), \
         patch.object(notifier, "_CHAT_ID", None), \
         patch.object(notifier.httpx, "AsyncClient", return_value=fake_client) as mock_cls:
        await notifier.notify_position_closed(make_closed_position(outcome="LOSS"))

    mock_cls.assert_not_called()
    fake_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_no_op_when_both_missing():
    fake_client = FakeAsyncClient()
    with patch.object(notifier, "_BOT_TOKEN", None), \
         patch.object(notifier, "_CHAT_ID", None), \
         patch.object(notifier.httpx, "AsyncClient", return_value=fake_client) as mock_cls:
        # Exercise every public notify_* function — none should raise or dispatch
        pos = make_closed_position()
        await notifier.notify_position_created(pos)
        await notifier.notify_position_filled(pos)
        await notifier.notify_position_closed(pos)
        await notifier.notify_risk_rejected("BTCUSDT", "LONG", "too much risk")
        await notifier.notify_circuit_breaker(80.0, 85.0)

    mock_cls.assert_not_called()


# ---------------------------------------------------------------------------
# HTTP failure — swallowed, never raised
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_http_error_is_swallowed():
    import httpx
    fake_client = FakeAsyncClient(post_side_effect=httpx.ConnectError("network down"))
    with patch.object(notifier, "_BOT_TOKEN", "test-token"), \
         patch.object(notifier, "_CHAT_ID", "12345"), \
         patch.object(notifier.httpx, "AsyncClient", return_value=fake_client):
        # Must not raise
        await notifier.notify_position_closed(make_closed_position(outcome="LOSS"))

    fake_client.post.assert_awaited_once()
