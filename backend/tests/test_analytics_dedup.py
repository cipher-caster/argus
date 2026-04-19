"""
C2: Backtest tab deduplication tests.

Verifies that the signal-log endpoint serves backtest data via source filter,
making a separate "Backtest" tab redundant. The SignalLog endpoint already
supports source filtering, and default behaviour excludes backtest signals.

All tests mock the database session — no live DB required.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_signal_row(
    id_: int = 1,
    symbol: str = "BTCUSDT",
    direction: str = "LONG",
    outcome: str = "WIN",
    source: str = "live",
    conviction: int = 75,
    fired_at: int = 1_704_067_200_000,
    market_state: str = "BULL",
    regime_at_resolution: str = None,
    rejection_reason: str = None,
):
    s = MagicMock()
    s.id = id_
    s.symbol = symbol
    s.direction = direction
    s.outcome = outcome
    s.source = source
    s.conviction = conviction
    s.fired_at = fired_at
    s.market_state = market_state
    s.regime_at_resolution = regime_at_resolution
    s.rejection_reason = rejection_reason
    s.time_to_resolution_ms = 14_400_000
    s.oracle_signal = "N/A"
    s.titan_signal = "BUY"
    s.oracle_score = 0
    s.titan_confidence = 80
    s.timeframe = "4h"
    s.entry = 50000.0
    s.tp = 51000.0
    s.sl = 49500.0
    s.fired_reason = "test signal"
    s.provider = "okx"
    s.resolved_at = None
    s.__dict__["__tablename__"] = "signal_log"
    return s


def _make_signal_log_session(signals, count=0, wins=0, losses=0, opens=0, reviews=0, rejected=0):
    """Mock async context manager for /signal-log (count + summary + data queries)."""
    mock_session = AsyncMock()

    count_result = MagicMock()
    count_result.scalar.return_value = count or len(signals)

    summary_row = MagicMock()
    summary_row.wins = wins
    summary_row.losses = losses
    summary_row.opens = opens
    summary_row.reviews = reviews
    summary_row.rejected = rejected
    summary_result = MagicMock()
    summary_result.one.return_value = summary_row

    data_result = MagicMock()
    data_result.scalars.return_value.all.return_value = signals

    mock_session.execute = AsyncMock(side_effect=[count_result, summary_result, data_result])
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


# ---------------------------------------------------------------------------
# C2: Source filter tests
# ---------------------------------------------------------------------------

class TestSignalLogSourceFilter:

    @pytest.mark.asyncio
    async def test_backtest_source_filter_returns_only_backtest(self, async_client):
        """source=backtest → only backtest signals returned."""
        backtest_signals = [
            _make_signal_row(id_=1, source="backtest", symbol="BTCUSDT"),
            _make_signal_row(id_=2, source="backtest", symbol="ETHUSDT"),
        ]

        ctx = _make_signal_log_session(
            backtest_signals, count=2, wins=1, losses=1
        )
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-log?source=backtest")

        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["total"] == 2
        assert body["summary"]["win"] == 1
        assert body["summary"]["loss"] == 1
        items = body["data"]
        assert len(items) == 2
        assert all(i["source"] == "backtest" for i in items)

    @pytest.mark.asyncio
    async def test_no_source_filter_excludes_backtest(self, async_client):
        """Default (no source param) → backtest signals excluded by the endpoint."""
        live_signals = [
            _make_signal_row(id_=1, source="live", symbol="BTCUSDT"),
        ]

        ctx = _make_signal_log_session(live_signals, count=1, wins=1)
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-log")

        assert resp.status_code == 200
        body = resp.json()
        items = body["data"]
        assert len(items) == 1
        assert items[0]["source"] == "live"

    @pytest.mark.asyncio
    async def test_live_source_filter(self, async_client):
        """source=live → only live signals returned."""
        live_signals = [
            _make_signal_row(id_=1, source="live", symbol="BTCUSDT"),
            _make_signal_row(id_=2, source="live", symbol="SOLUSDT"),
        ]

        ctx = _make_signal_log_session(live_signals, count=2, wins=2)
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-log?source=live")

        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["total"] == 2
        items = body["data"]
        assert all(i["source"] == "live" for i in items)

    @pytest.mark.asyncio
    async def test_scanner_source_filter(self, async_client):
        """source=scanner → only scanner signals returned."""
        scanner_signals = [
            _make_signal_row(id_=1, source="scanner", symbol="ETHUSDT"),
        ]

        ctx = _make_signal_log_session(scanner_signals, count=1, wins=1)
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-log?source=scanner")

        assert resp.status_code == 200
        body = resp.json()
        items = body["data"]
        assert len(items) == 1
        assert items[0]["source"] == "scanner"


# ---------------------------------------------------------------------------
# C2: Symbol filter tests
# ---------------------------------------------------------------------------

class TestSignalLogSymbolFilter:

    @pytest.mark.asyncio
    async def test_symbol_filter(self, async_client):
        """symbol=BTC → only BTCUSDT signals returned."""
        btc_signals = [
            _make_signal_row(id_=1, symbol="BTCUSDT", source="live"),
        ]

        ctx = _make_signal_log_session(btc_signals, count=1, wins=1)
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-log?symbol=BTC")

        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["total"] == 1
        items = body["data"]
        assert all(i["symbol"] == "BTCUSDT" for i in items)

    @pytest.mark.asyncio
    async def test_symbol_and_source_filter_combined(self, async_client):
        """symbol=BTC&source=backtest → BTCUSDT backtest signals only."""
        signals = [
            _make_signal_row(id_=1, symbol="BTCUSDT", source="backtest"),
        ]

        ctx = _make_signal_log_session(signals, count=1, wins=1)
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get(
                "/api/analytics/signal-log?symbol=BTC&source=backtest"
            )

        assert resp.status_code == 200
        body = resp.json()
        items = body["data"]
        assert len(items) == 1
        assert items[0]["symbol"] == "BTCUSDT"
        assert items[0]["source"] == "backtest"


# ---------------------------------------------------------------------------
# C2: Pagination
# ---------------------------------------------------------------------------

class TestSignalLogPagination:

    @pytest.mark.asyncio
    async def test_pagination_params_accepted(self, async_client):
        """limit and offset params are passed through to the query."""
        signals = [_make_signal_row(id_=i) for i in range(5)]

        ctx = _make_signal_log_session(signals, count=20, wins=10, losses=5, opens=5)
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get(
                "/api/analytics/signal-log?limit=5&offset=10"
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 20
        assert len(body["data"]) == 5

    @pytest.mark.asyncio
    async def test_empty_result_safe_defaults(self, async_client):
        """No signals → empty data list, zero counts."""
        ctx = _make_signal_log_session([], count=0, wins=0, losses=0, opens=0)
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-log?source=backtest")

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"] == []
        assert body["summary"]["total"] == 0
        assert body["summary"]["win_rate"] is None


# ---------------------------------------------------------------------------
# C2: Signal-log stats (backtest leaderboard)
# ---------------------------------------------------------------------------

class TestSignalLogStats:

    @pytest.mark.asyncio
    async def test_stats_endpoint_returns_leaderboard(self, async_client):
        """/signal-log/stats returns per-coin aggregated stats for backtest source."""
        signals = [
            _make_signal_row(id_=1, symbol="BTCUSDT", source="backtest", outcome="WIN", direction="LONG"),
            _make_signal_row(id_=2, symbol="BTCUSDT", source="backtest", outcome="LOSS", direction="LONG"),
            _make_signal_row(id_=3, symbol="ETHUSDT", source="backtest", outcome="WIN", direction="SHORT"),
        ]

        for s in signals:
            s.entry = 50000.0
            s.tp = 51000.0
            s.sl = 49500.0

        mock_session = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = signals
        mock_session.execute = AsyncMock(return_value=result)
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=mock_session)
        ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-log/stats?source=backtest")

        assert resp.status_code == 200
        body = resp.json()
        assert "coins" in body
        assert len(body["coins"]) == 2
        coin_symbols = [c["symbol"] for c in body["coins"]]
        assert "BTCUSDT" in coin_symbols
        assert "ETHUSDT" in coin_symbols

    @pytest.mark.asyncio
    async def test_stats_empty_returns_safe_defaults(self, async_client):
        """/signal-log/stats with no data → empty coins, None overall."""
        mock_session = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=result)
        ctx = MagicMock()
        ctx.__aenter__ = AsyncMock(return_value=mock_session)
        ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-log/stats?source=backtest")

        assert resp.status_code == 200
        body = resp.json()
        assert body["coins"] == []
        assert body["overall"] is None
