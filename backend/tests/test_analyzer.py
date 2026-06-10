"""
A3: TradeAnalyzer unit tests.

Tests _bucket(), _coin_stats(), streak analysis, backtest-vs-live comparison,
and empty-positions handling — all with mocked DB sessions.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.trading.analyzer import TradeAnalyzer, _bucket, _coin_stats

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_position(
    outcome: str,
    symbol: str = "BTCUSDT",
    conviction: int = 65,
    intended_entry: float = 100.0,
    intended_tp: float = 106.0,
    intended_sl: float = 97.0,
    filled_at=None,
    closed_at=None,
    market_state: str = "BEAR",
    direction: str = "SHORT",
):
    pos = MagicMock()
    pos.outcome = outcome
    pos.symbol = symbol
    pos.conviction = conviction
    pos.intended_entry = intended_entry
    pos.intended_tp = intended_tp
    pos.intended_sl = intended_sl
    pos.filled_at = filled_at
    pos.closed_at = closed_at
    pos.market_state = market_state
    pos.direction = direction
    pos.status = "CLOSED"
    return pos


def make_signal_log(outcome: str, symbol: str = "BTCUSDT"):
    s = MagicMock()
    s.outcome = outcome
    s.symbol = symbol
    s.source = "backtest"
    return s


def _mock_session_ctx(positions, rejections=None):
    """Return a mock async context manager that returns positions then rejections."""
    if rejections is None:
        rejections = []
    mock_session = AsyncMock()
    pos_result = MagicMock()
    pos_result.scalars.return_value.all.return_value = positions
    rej_result = MagicMock()
    rej_result.scalars.return_value.all.return_value = rejections
    mock_session.execute = AsyncMock(side_effect=[pos_result, rej_result])
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


def _mock_compare_ctx(bt_signals, live_positions):
    """Return a mock context for compare_backtest_vs_live (2 executes)."""
    mock_session = AsyncMock()
    bt_result = MagicMock()
    bt_result.scalars.return_value.all.return_value = bt_signals
    live_result = MagicMock()
    live_result.scalars.return_value.all.return_value = live_positions
    mock_session.execute = AsyncMock(side_effect=[bt_result, live_result])
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


# ---------------------------------------------------------------------------
# A3: _bucket
# ---------------------------------------------------------------------------


class TestBucketFunction:
    def test_high_conviction(self):
        assert _bucket(75) == "75+"
        assert _bucket(80) == "75+"
        assert _bucket(100) == "75+"

    def test_medium_conviction(self):
        assert _bucket(65) == "65-74"
        assert _bucket(70) == "65-74"
        assert _bucket(74) == "65-74"

    def test_low_conviction(self):
        assert _bucket(55) == "55-64"
        assert _bucket(64) == "55-64"
        assert _bucket(0) == "55-64"


# ---------------------------------------------------------------------------
# A3: _coin_stats
# ---------------------------------------------------------------------------


class TestCoinStats:
    def test_win_rate_two_wins_one_loss(self):
        positions = [
            make_position("WIN"),
            make_position("WIN"),
            make_position("LOSS"),
        ]
        stats = _coin_stats(positions)
        assert stats["wins"] == 2
        assert stats["losses"] == 1
        assert stats["win_rate"] == pytest.approx(66.7, rel=0.01)

    def test_profit_r_on_win(self):
        # RR = (106-100)/(100-97) = 6/3 = 2.0
        stats = _coin_stats(
            [make_position("WIN", intended_entry=100, intended_tp=106, intended_sl=97)]
        )
        assert stats["profit_r"] == pytest.approx(2.0, rel=0.01)

    def test_profit_r_minus_one_on_loss(self):
        stats = _coin_stats([make_position("LOSS")])
        assert stats["profit_r"] == pytest.approx(-1.0)

    def test_avg_hold_hours(self):
        # filled_at must be non-zero (0 is falsy, skipped by _coin_stats)
        base_ms = 1_704_067_200_000
        pos = make_position("WIN", filled_at=base_ms, closed_at=base_ms + 4 * 3_600_000)
        stats = _coin_stats([pos])
        assert stats["avg_hold_hours"] == pytest.approx(4.0)

    def test_no_closed_trades_win_rate_is_none(self):
        stats = _coin_stats([make_position("REVIEW")])
        assert stats["win_rate"] is None
        assert stats["count"] == 1


# ---------------------------------------------------------------------------
# A3: streak analysis (via analyze_closed_trades)
# ---------------------------------------------------------------------------


class TestStreakAnalysis:
    @pytest.mark.asyncio
    async def test_longest_win_streak_detected(self):
        positions = [
            make_position("WIN", closed_at=1000),
            make_position("WIN", closed_at=2000),
            make_position("WIN", closed_at=3000),
            make_position("LOSS", closed_at=4000),
        ]
        with patch(
            "app.trading.analyzer.Database.get_session", return_value=_mock_session_ctx(positions)
        ):
            result = await TradeAnalyzer.analyze_closed_trades()

        streak = result["streak_analysis"]
        assert streak["longest_win_streak"] == 3
        assert streak["longest_loss_streak"] == 1
        assert streak["current_streak"]["type"] == "LOSS"
        assert streak["current_streak"]["length"] == 1

    @pytest.mark.asyncio
    async def test_longest_loss_streak_detected(self):
        positions = [
            make_position("WIN", closed_at=1000),
            make_position("LOSS", closed_at=2000),
            make_position("LOSS", closed_at=3000),
            make_position("LOSS", closed_at=4000),
        ]
        with patch(
            "app.trading.analyzer.Database.get_session", return_value=_mock_session_ctx(positions)
        ):
            result = await TradeAnalyzer.analyze_closed_trades()

        streak = result["streak_analysis"]
        assert streak["longest_loss_streak"] == 3
        assert streak["current_streak"]["type"] == "LOSS"

    @pytest.mark.asyncio
    async def test_empty_positions_returns_safe_defaults(self):
        with patch("app.trading.analyzer.Database.get_session", return_value=_mock_session_ctx([])):
            result = await TradeAnalyzer.analyze_closed_trades()

        assert result["total_closed"] == 0
        assert "message" in result
        assert result["by_symbol"] == {}


# ---------------------------------------------------------------------------
# A3: compare_backtest_vs_live
# ---------------------------------------------------------------------------


class TestCompareBacktestVsLive:
    @pytest.mark.asyncio
    async def test_divergence_flagged_when_over_15pct(self):
        """backtest 0% WR, live 100% WR → divergence=100, flagged=True."""
        bt = [make_signal_log("LOSS", "BTCUSDT")]
        live = [make_position("WIN", symbol="BTCUSDT")]

        with patch(
            "app.trading.analyzer.Database.get_session", return_value=_mock_compare_ctx(bt, live)
        ):
            result = await TradeAnalyzer.compare_backtest_vs_live()

        assert result["BTCUSDT"]["flagged"] is True
        assert result["BTCUSDT"]["divergence"] == pytest.approx(100.0)

    @pytest.mark.asyncio
    async def test_no_divergence_not_flagged(self):
        """Both backtest and live at 50% WR → divergence=0, flagged=False."""
        bt = [make_signal_log("WIN", "XRPUSDT"), make_signal_log("LOSS", "XRPUSDT")]
        live = [make_position("WIN", symbol="XRPUSDT"), make_position("LOSS", symbol="XRPUSDT")]

        with patch(
            "app.trading.analyzer.Database.get_session", return_value=_mock_compare_ctx(bt, live)
        ):
            result = await TradeAnalyzer.compare_backtest_vs_live()

        assert result["XRPUSDT"]["flagged"] is False
        assert result["XRPUSDT"]["divergence"] == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_backtest_only_symbol_has_no_live_wr(self):
        """Symbol in backtest but not live → live_wr=None, not flagged."""
        bt = [make_signal_log("WIN", "SOLUSDT")]
        live = []

        with patch(
            "app.trading.analyzer.Database.get_session", return_value=_mock_compare_ctx(bt, live)
        ):
            result = await TradeAnalyzer.compare_backtest_vs_live()

        assert result["SOLUSDT"]["live_wr"] is None
        assert result["SOLUSDT"]["flagged"] is False
