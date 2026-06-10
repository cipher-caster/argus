"""
Tests for backtest_engine.py — tiebreaker logic.

Covers:
- _tiebreaker_5m_from_db: 5min candle tiebreaker for same-candle TP+SL
- resolve_outcome_with_tiebreaker: async resolver that delegates to tiebreaker
- resolve_outcome (sync): conservative fallback (existing behavior preserved)
"""

from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_4h_df(candles):
    """
    Build a minimal 4H DataFrame.
    candles: list of (ts_ms, open, high, low, close)
    """
    rows = []
    for ts_ms, o, h, l, c in candles:
        rows.append(
            {
                "timestamp": pd.Timestamp(ts_ms, unit="ms", tz="UTC"),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": 100.0,
                "ts_ms": ts_ms,
            }
        )
    return pd.DataFrame(rows)


def _make_5m_df(candles):
    """
    Build a minimal 5min DataFrame.
    candles: list of (ts_ms, high, low)
    """
    rows = []
    for ts_ms, h, l in candles:
        rows.append(
            {
                "timestamp": pd.Timestamp(ts_ms, unit="ms", tz="UTC"),
                "open": 0,
                "high": h,
                "low": l,
                "close": 0,
                "volume": 10.0,
                "ts_ms": ts_ms,
            }
        )
    return pd.DataFrame(rows)


BASE_MS = 1700000000000  # arbitrary base


# ---------------------------------------------------------------------------
# TestTiebreaker5mFromDb
# ---------------------------------------------------------------------------


class TestTiebreaker5mFromDb:
    @pytest.mark.asyncio
    @patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock)
    async def test_tp_hit_first_returns_win(self, mock_load):
        """5min data: TP hit before SL → WIN at TP price."""
        from app.trading.backtest_engine import _tiebreaker_5m_from_db

        # LONG: tp=110, sl=90
        mock_load.return_value = _make_5m_df(
            [
                (BASE_MS, 105.0, 95.0),  # neither
                (BASE_MS + 300000, 112.0, 98.0),  # TP hit!
                (BASE_MS + 600000, 108.0, 88.0),  # SL hit after
            ]
        )

        result = await _tiebreaker_5m_from_db("BTC/USDT", "LONG", 110.0, 90.0, BASE_MS)
        assert result["outcome"] == "WIN"
        assert result["resolved_price"] == 110.0
        assert result["resolved_at_ms"] == BASE_MS + 300000

    @pytest.mark.asyncio
    @patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock)
    async def test_sl_hit_first_returns_loss(self, mock_load):
        """5min data: SL hit before TP → LOSS at SL price."""
        from app.trading.backtest_engine import _tiebreaker_5m_from_db

        mock_load.return_value = _make_5m_df(
            [
                (BASE_MS, 105.0, 88.0),  # SL hit!
                (BASE_MS + 300000, 112.0, 85.0),
            ]
        )

        result = await _tiebreaker_5m_from_db("BTC/USDT", "LONG", 110.0, 90.0, BASE_MS)
        assert result["outcome"] == "LOSS"
        assert result["resolved_price"] == 90.0
        assert result["resolved_at_ms"] == BASE_MS

    @pytest.mark.asyncio
    @patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock)
    async def test_short_tp_hit_first(self, mock_load):
        """SHORT: 5min data — TP hit first (low <= tp) → WIN."""
        from app.trading.backtest_engine import _tiebreaker_5m_from_db

        # SHORT: tp=90, sl=110
        mock_load.return_value = _make_5m_df(
            [
                (BASE_MS, 105.0, 88.0),  # low=88 <= tp=90 → TP hit
                (BASE_MS + 300000, 112.0, 85.0),
            ]
        )

        result = await _tiebreaker_5m_from_db("BTC/USDT", "SHORT", 90.0, 110.0, BASE_MS)
        assert result["outcome"] == "WIN"
        assert result["resolved_price"] == 90.0

    @pytest.mark.asyncio
    @patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock)
    async def test_no_5m_data_falls_back_to_loss(self, mock_load):
        """No 5min data in DB → conservative LOSS."""
        from app.trading.backtest_engine import _tiebreaker_5m_from_db

        mock_load.return_value = pd.DataFrame()

        result = await _tiebreaker_5m_from_db("BTC/USDT", "LONG", 110.0, 90.0, BASE_MS)
        assert result["outcome"] == "LOSS"
        assert result["resolved_price"] == 90.0
        assert result["resolved_at_ms"] == BASE_MS

    @pytest.mark.asyncio
    @patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock)
    async def test_both_hit_same_5m_candle_skips(self, mock_load):
        """Both hit in same 5m candle → skip, check next candle."""
        from app.trading.backtest_engine import _tiebreaker_5m_from_db

        mock_load.return_value = _make_5m_df(
            [
                (BASE_MS, 112.0, 88.0),  # both hit — skip
                (BASE_MS + 300000, 112.0, 95.0),  # TP only
            ]
        )

        result = await _tiebreaker_5m_from_db("BTC/USDT", "LONG", 110.0, 90.0, BASE_MS)
        assert result["outcome"] == "WIN"
        assert result["resolved_at_ms"] == BASE_MS + 300000


# ---------------------------------------------------------------------------
# TestResolveOutcomeWithTiebreaker
# ---------------------------------------------------------------------------


class TestResolveOutcomeWithTiebreaker:
    @pytest.mark.asyncio
    @patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock)
    async def test_normal_sl_hit(self, mock_load):
        """SL hit alone (no TP in same candle) → LOSS without tiebreaker call."""
        from app.trading.backtest_engine import resolve_outcome_with_tiebreaker

        df = _make_4h_df(
            [
                (BASE_MS, 100, 105, 95, 100),
                (BASE_MS + 14400000, 100, 102, 88, 90),  # low=88 <= sl=90
            ]
        )

        outcome, price, ts = await resolve_outcome_with_tiebreaker(
            df,
            0,
            "LONG",
            110.0,
            90.0,
            "BTC/USDT",
            42,
        )
        assert outcome == "LOSS"
        assert price == 90.0
        # load_candles should NOT have been called (no tiebreaker needed)
        mock_load.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock)
    async def test_normal_tp_hit(self, mock_load):
        """TP hit alone (no SL in same candle) → WIN without tiebreaker call."""
        from app.trading.backtest_engine import resolve_outcome_with_tiebreaker

        df = _make_4h_df(
            [
                (BASE_MS, 100, 105, 95, 100),
                (BASE_MS + 14400000, 100, 112, 96, 110),  # high=112 >= tp=110
            ]
        )

        outcome, price, ts = await resolve_outcome_with_tiebreaker(
            df,
            0,
            "LONG",
            110.0,
            90.0,
            "BTC/USDT",
            42,
        )
        assert outcome == "WIN"
        assert price == 110.0
        mock_load.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock)
    async def test_same_candle_uses_tiebreaker(self, mock_load):
        """Both TP+SL hit in same 4H candle → delegates to 5min tiebreaker."""
        from app.trading.backtest_engine import resolve_outcome_with_tiebreaker

        df = _make_4h_df(
            [
                (BASE_MS, 100, 105, 95, 100),
                (BASE_MS + 14400000, 100, 112, 88, 105),  # high=112>=tp=110, low=88<=sl=90
            ]
        )

        mock_load.return_value = _make_5m_df(
            [
                (BASE_MS + 14400000, 102, 96),
                (BASE_MS + 14400000 + 300000, 112, 98),  # TP hit first
                (BASE_MS + 14400000 + 600000, 108, 88),  # SL hit after
            ]
        )

        outcome, price, ts = await resolve_outcome_with_tiebreaker(
            df,
            0,
            "LONG",
            110.0,
            90.0,
            "BTC/USDT",
            42,
        )
        assert outcome == "WIN"
        assert price == 110.0
        mock_load.assert_called_once_with("BTC/USDT", "5m")

    @pytest.mark.asyncio
    @patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock)
    async def test_review_when_no_hit(self, mock_load):
        """Neither TP nor SL hit within max_hold → REVIEW."""
        from app.trading.backtest_engine import resolve_outcome_with_tiebreaker

        df = _make_4h_df(
            [
                (BASE_MS, 100, 105, 95, 100),
                (BASE_MS + 14400000, 100, 105, 96, 102),  # no hit
            ]
        )

        outcome, price, ts = await resolve_outcome_with_tiebreaker(
            df,
            0,
            "LONG",
            110.0,
            90.0,
            "BTC/USDT",
            1,
        )
        assert outcome == "REVIEW"
        assert price is None
        mock_load.assert_not_called()


# ---------------------------------------------------------------------------
# TestResolveOutcomeSync — verify sync function still works (backward compat)
# ---------------------------------------------------------------------------


class TestResolveOutcomeSync:
    def test_conservative_same_candle(self):
        """Sync resolve_outcome: both hit in same candle → conservative LOSS."""
        from app.trading.backtest_engine import resolve_outcome

        df = _make_4h_df(
            [
                (BASE_MS, 100, 105, 95, 100),
                (BASE_MS + 14400000, 100, 112, 88, 105),
            ]
        )

        outcome, price, ts = resolve_outcome(df, 0, "LONG", 110.0, 90.0, 42)
        assert outcome == "LOSS"
        assert price == 90.0

    def test_tp_hit_alone(self):
        """Sync resolve_outcome: TP hit alone → WIN."""
        from app.trading.backtest_engine import resolve_outcome

        df = _make_4h_df(
            [
                (BASE_MS, 100, 105, 95, 100),
                (BASE_MS + 14400000, 100, 112, 96, 110),
            ]
        )

        outcome, price, ts = resolve_outcome(df, 0, "LONG", 110.0, 90.0, 42)
        assert outcome == "WIN"
        assert price == 110.0
