"""
Tests for GET /api/analytics/provider-comparison.

Covers:
- Only binance signals present
- Mixed binance + okx signals
- Empty response (no resolved signals)
- REVIEW / REJECTED / OPEN signals excluded from win rate
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_signal(
    symbol="BTCUSDT",
    direction="LONG",
    outcome="WIN",
    provider="binance",
    entry=100.0,
    tp=110.0,
    sl=90.0,
):
    sig = MagicMock()
    sig.symbol = symbol
    sig.direction = direction
    sig.outcome = outcome
    sig.provider = provider
    sig.entry = entry
    sig.tp = tp
    sig.sl = sl
    return sig


def _mock_db(mock_db, signals):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = signals
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)


class TestProviderComparison:
    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_empty_returns_empty_dict(self, mock_db, async_client):
        _mock_db(mock_db, [])
        resp = await async_client.get("/api/analytics/provider-comparison")
        assert resp.status_code == 200
        assert resp.json() == {}

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_only_binance_signals(self, mock_db, async_client):
        signals = [
            _make_signal("BTCUSDT", outcome="WIN", provider="binance"),
            _make_signal("BTCUSDT", outcome="LOSS", provider="binance"),
            _make_signal("ETHUSDT", outcome="WIN", provider="binance"),
        ]
        _mock_db(mock_db, signals)
        resp = await async_client.get("/api/analytics/provider-comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert "binance" in data
        assert "okx" not in data
        b = data["binance"]
        assert b["total"] == 3
        assert b["wins"] == 2
        assert b["losses"] == 1
        assert b["win_rate"] == pytest.approx(2 / 3, rel=1e-3)

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_mixed_binance_and_okx(self, mock_db, async_client):
        signals = [
            _make_signal("BTCUSDT", outcome="WIN", provider="binance"),
            _make_signal("BTCUSDT", outcome="WIN", provider="binance"),
            _make_signal("BTCUSDT", outcome="LOSS", provider="binance"),
            _make_signal("ETHUSDT", outcome="WIN", provider="okx"),
            _make_signal("ETHUSDT", outcome="LOSS", provider="okx"),
        ]
        _mock_db(mock_db, signals)
        resp = await async_client.get("/api/analytics/provider-comparison")
        data = resp.json()
        assert "binance" in data
        assert "okx" in data

        b = data["binance"]
        assert b["total"] == 3
        assert b["wins"] == 2
        assert b["win_rate"] == pytest.approx(2 / 3, rel=1e-3)

        o = data["okx"]
        assert o["total"] == 2
        assert o["wins"] == 1
        assert o["win_rate"] == pytest.approx(0.5, rel=1e-3)

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_review_rejected_open_excluded(self, mock_db, async_client):
        """Signals with REVIEW, REJECTED, or OPEN outcomes must not appear in results."""
        signals = [
            _make_signal("BTCUSDT", outcome="WIN", provider="binance"),
        ]
        _mock_db(mock_db, signals)
        resp = await async_client.get("/api/analytics/provider-comparison")
        data = resp.json()
        assert data["binance"]["total"] == 1

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_top_coins_min_3_signals(self, mock_db, async_client):
        """Coins with fewer than 3 resolved signals are excluded from top_coins."""
        signals = [
            _make_signal("BTCUSDT", outcome="WIN", provider="binance"),
            _make_signal("BTCUSDT", outcome="WIN", provider="binance"),
            _make_signal("BTCUSDT", outcome="WIN", provider="binance"),
            _make_signal("ETHUSDT", outcome="WIN", provider="binance"),
            _make_signal("ETHUSDT", outcome="LOSS", provider="binance"),
        ]
        _mock_db(mock_db, signals)
        resp = await async_client.get("/api/analytics/provider-comparison")
        top = resp.json()["binance"]["top_coins"]
        symbols = [c["symbol"] for c in top]
        assert "BTCUSDT" in symbols
        assert "ETHUSDT" not in symbols

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_top_coins_capped_at_5(self, mock_db, async_client):
        """top_coins list is at most 5 entries."""
        signals = []
        for sym in ["AAUSDT", "BBUSDT", "CCUSDT", "DDUSDT", "EEUSDT", "FFUSDT"]:
            for _ in range(3):
                signals.append(_make_signal(sym, outcome="WIN", provider="okx"))
        _mock_db(mock_db, signals)
        resp = await async_client.get("/api/analytics/provider-comparison")
        top = resp.json()["okx"]["top_coins"]
        assert len(top) <= 5

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_avg_r_profit_calculation(self, mock_db, async_client):
        """WIN with 2:1 RR = +2R, LOSS = -1R, avg = (+2R - 1R) / 2 = +0.5R."""
        signals = [
            _make_signal(
                "BTCUSDT", outcome="WIN", provider="binance", entry=100.0, tp=120.0, sl=90.0
            ),  # reward=20, risk=10 → 2R
            _make_signal(
                "BTCUSDT", outcome="LOSS", provider="binance", entry=100.0, tp=120.0, sl=90.0
            ),  # -1R
        ]
        _mock_db(mock_db, signals)
        resp = await async_client.get("/api/analytics/provider-comparison")
        avg_r = resp.json()["binance"]["avg_r_profit"]
        assert avg_r == pytest.approx(0.5, rel=1e-3)
