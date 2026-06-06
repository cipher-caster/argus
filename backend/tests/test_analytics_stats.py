"""
Tests for signal log stats endpoint (/api/analytics/signal-log/stats).

Covers per-coin aggregation, L/S split, R-profit math, source filtering,
overall stats, and edge cases.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_signal(symbol="BTCUSDT", direction="LONG", outcome="WIN",
                 source="backtest", entry=100.0, tp=110.0, sl=90.0,
                 conviction=70):
    sig = MagicMock()
    sig.symbol = symbol
    sig.direction = direction
    sig.outcome = outcome
    sig.source = source
    sig.entry = entry
    sig.tp = tp
    sig.sl = sl
    sig.conviction = conviction
    return sig


class TestSignalLogStats:

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_returns_empty_when_no_data(self, mock_db, async_client):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/analytics/signal-log/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["coins"] == []
        assert data["overall"] is None

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_aggregates_per_coin(self, mock_db, async_client):
        signals = [
            _make_signal("BTCUSDT", "LONG", "WIN"),
            _make_signal("BTCUSDT", "LONG", "LOSS"),
            _make_signal("ETHUSDT", "SHORT", "WIN"),
        ]
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = signals
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/analytics/signal-log/stats")
        data = resp.json()
        assert len(data["coins"]) == 2
        btc = next(c for c in data["coins"] if c["symbol"] == "BTCUSDT")
        assert btc["wins"] == 1
        assert btc["losses"] == 1
        assert btc["win_rate"] == 50.0

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_long_short_split(self, mock_db, async_client):
        signals = [
            _make_signal("BTCUSDT", "LONG", "WIN"),
            _make_signal("BTCUSDT", "LONG", "WIN"),
            _make_signal("BTCUSDT", "SHORT", "LOSS"),
        ]
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = signals
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/analytics/signal-log/stats")
        btc = resp.json()["coins"][0]
        assert btc["long_wr"] == 100.0
        assert btc["short_wr"] == 0.0

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_r_profit_calculation(self, mock_db, async_client):
        """WIN with 2:1 RR = +2R, LOSS = -1R, net = +1R."""
        signals = [
            _make_signal("BTCUSDT", "LONG", "WIN", entry=100.0, tp=120.0, sl=90.0),  # RR=2.0
            _make_signal("BTCUSDT", "LONG", "LOSS", entry=100.0, tp=120.0, sl=90.0),  # -1R
        ]
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = signals
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/analytics/signal-log/stats")
        btc = resp.json()["coins"][0]
        assert btc["profit_r"] == 1.0  # +2R - 1R = +1R

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_filters_by_source(self, mock_db, async_client):
        """Only backtest source rows returned when source=backtest."""
        signals = [_make_signal(source="backtest")]
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = signals
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/analytics/signal-log/stats?source=backtest")
        assert resp.status_code == 200
        assert len(resp.json()["coins"]) == 1

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_overall_stats(self, mock_db, async_client):
        signals = [
            _make_signal("BTCUSDT", outcome="WIN"),
            _make_signal("BTCUSDT", outcome="LOSS"),
            _make_signal("ETHUSDT", outcome="WIN"),
        ]
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = signals
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/analytics/signal-log/stats")
        overall = resp.json()["overall"]
        assert overall["total_signals"] == 3
        assert overall["total_coins"] == 2
        assert overall["win_rate"] == 66.7  # 2 wins / 3 closed

    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_handles_zero_closed(self, mock_db, async_client):
        """All OPEN/REVIEW → win_rate is null."""
        signals = [
            _make_signal(outcome="OPEN"),
            _make_signal(outcome="REVIEW"),
        ]
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = signals
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/analytics/signal-log/stats")
        btc = resp.json()["coins"][0]
        assert btc["win_rate"] is None
