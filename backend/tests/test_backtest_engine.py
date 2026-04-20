"""
A1: Backtest Engine unit tests.

Tests resolve_outcome() and compute_stats() in isolation — no DB, no network.
Covers: LONG/SHORT WIN/LOSS, same-candle tiebreak (conservative LOSS),
REVIEW on max_hold expiry, and stats aggregation.
"""
import pandas as pd
import pytest
from app.trading.backtest_engine import resolve_outcome, compute_stats
from app.utils.trading_utils import calculate_conviction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_candles(rows: list[dict]) -> pd.DataFrame:
    """Build a minimal 4H candle DataFrame from a list of high/low dicts."""
    base_ms = 1_704_067_200_000  # 2024-01-01 00:00 UTC
    data = []
    for i, r in enumerate(rows):
        price = r.get("close", 100.0)
        data.append({
            "timestamp": pd.Timestamp(base_ms + i * 14_400_000, unit="ms", tz="UTC"),
            "open": price,
            "high": r["high"],
            "low": r["low"],
            "close": price,
            "volume": 1000.0,
            "ts_ms": base_ms + i * 14_400_000,
        })
    return pd.DataFrame(data)


def _signal(outcome: str, entry=100.0, tp=106.0, sl=97.0, symbol="BTCUSDT") -> dict:
    return {"symbol": symbol, "outcome": outcome, "entry": entry, "tp": tp, "sl": sl}


# ---------------------------------------------------------------------------
# A1: resolve_outcome — candle-walk logic
# ---------------------------------------------------------------------------

class TestResolveOutcome:

    def test_long_win_outcome(self):
        """LONG: price reaches TP before SL → WIN."""
        df = make_candles([
            {"high": 104.0, "low": 98.0},   # entry idx=0 (not checked)
            {"high": 112.0, "low": 101.0},  # TP=110 hit
        ])
        outcome, price, ts = resolve_outcome(df, entry_idx=0, direction="LONG", tp=110.0, sl=95.0)
        assert outcome == "WIN"
        assert price == 110.0
        assert ts is not None

    def test_long_loss_outcome(self):
        """LONG: price drops below SL → LOSS."""
        df = make_candles([
            {"high": 104.0, "low": 98.0},
            {"high": 103.0, "low": 93.0},  # SL=95 hit
        ])
        outcome, price, ts = resolve_outcome(df, entry_idx=0, direction="LONG", tp=110.0, sl=95.0)
        assert outcome == "LOSS"
        assert price == 95.0

    def test_short_win_outcome(self):
        """SHORT: price drops to TP → WIN."""
        df = make_candles([
            {"high": 101.0, "low": 95.0},
            {"high": 99.0, "low": 88.0},   # TP=90 hit (low <= tp)
        ])
        outcome, price, ts = resolve_outcome(df, entry_idx=0, direction="SHORT", tp=90.0, sl=105.0)
        assert outcome == "WIN"
        assert price == 90.0

    def test_short_loss_outcome(self):
        """SHORT: price rises above SL → LOSS."""
        df = make_candles([
            {"high": 101.0, "low": 95.0},
            {"high": 107.0, "low": 99.0},  # SL=105 hit (high >= sl)
        ])
        outcome, price, ts = resolve_outcome(df, entry_idx=0, direction="SHORT", tp=90.0, sl=105.0)
        assert outcome == "LOSS"
        assert price == 105.0

    def test_both_hit_same_candle_is_loss(self):
        """Same candle hits both TP and SL → conservative LOSS."""
        df = make_candles([
            {"high": 104.0, "low": 98.0},
            {"high": 115.0, "low": 88.0},  # Both TP=110 and SL=92 crossed
        ])
        outcome, price, ts = resolve_outcome(df, entry_idx=0, direction="LONG", tp=110.0, sl=92.0)
        assert outcome == "LOSS"
        assert price == 92.0

    def test_short_both_hit_same_candle_is_loss(self):
        """SHORT same-candle both hit → conservative LOSS."""
        df = make_candles([
            {"high": 101.0, "low": 95.0},
            {"high": 115.0, "low": 82.0},  # Both SL=110 and TP=85 hit
        ])
        outcome, price, ts = resolve_outcome(df, entry_idx=0, direction="SHORT", tp=85.0, sl=110.0)
        assert outcome == "LOSS"
        assert price == 110.0

    def test_review_when_max_hold_exceeded(self):
        """No resolution within max_hold candles → REVIEW."""
        # Tight candles that never touch tp=110 or sl=90
        df = make_candles([{"high": 102.0, "low": 98.0}] * 20)
        outcome, price, ts = resolve_outcome(
            df, entry_idx=0, direction="LONG", tp=110.0, sl=90.0, max_hold=5
        )
        assert outcome == "REVIEW"
        assert price is None
        assert ts is None

    def test_review_at_end_of_data(self):
        """Only one candle (entry) — no future candles → REVIEW."""
        df = make_candles([{"high": 102.0, "low": 98.0}])
        outcome, price, ts = resolve_outcome(
            df, entry_idx=0, direction="LONG", tp=110.0, sl=90.0
        )
        assert outcome == "REVIEW"


# ---------------------------------------------------------------------------
# A1: compute_stats — aggregation
# ---------------------------------------------------------------------------

class TestComputeStats:

    def test_empty_returns_zero_stats(self):
        result = compute_stats([])
        assert result["total"] == 0
        assert result["wins"] == 0
        assert result["losses"] == 0
        assert result["win_rate"] is None
        assert result["total_r"] == 0.0
        assert result["ev_per_trade"] is None

    def test_all_wins(self):
        signals = [_signal("WIN")] * 4
        result = compute_stats(signals)
        assert result["wins"] == 4
        assert result["losses"] == 0
        assert result["win_rate"] == 100.0
        assert result["total_r"] > 0

    def test_all_losses(self):
        signals = [_signal("LOSS")] * 3
        result = compute_stats(signals)
        assert result["wins"] == 0
        assert result["losses"] == 3
        assert result["win_rate"] == 0.0
        assert result["total_r"] == pytest.approx(-3.0)

    def test_mixed_outcomes_win_rate(self):
        signals = [
            _signal("WIN"),
            _signal("WIN"),
            _signal("LOSS"),
            _signal("REVIEW"),   # reviews excluded from win_rate denominator
        ]
        result = compute_stats(signals)
        assert result["total"] == 4
        assert result["wins"] == 2
        assert result["losses"] == 1
        assert result["reviews"] == 1
        # win_rate = 2 / (2+1) = 66.67%
        assert result["win_rate"] == pytest.approx(66.67, rel=0.01)

    def test_per_coin_breakdown(self):
        signals = [
            _signal("WIN",  symbol="BTCUSDT"),
            _signal("WIN",  symbol="BTCUSDT"),
            _signal("LOSS", symbol="ETHUSDT"),
        ]
        result = compute_stats(signals)
        btc = result["coin_results"]["BTCUSDT"]
        eth = result["coin_results"]["ETHUSDT"]
        assert btc["wins"] == 2
        assert btc["losses"] == 0
        assert btc["win_rate"] == 100.0
        assert eth["wins"] == 0
        assert eth["losses"] == 1
        assert eth["profit_r"] == pytest.approx(-1.0)

    def test_rr_included_in_total_r(self):
        # entry=100, tp=106, sl=97 → RR = 6/3 = 2.0
        signals = [_signal("WIN", entry=100.0, tp=106.0, sl=97.0)]
        result = compute_stats(signals)
        assert result["total_r"] == pytest.approx(2.0, rel=0.01)
        assert result["avg_rr"] == pytest.approx(2.0, rel=0.01)


# ---------------------------------------------------------------------------
# A1: TestBacktestConviction — conviction formula unit tests
# ---------------------------------------------------------------------------

class TestBacktestConviction:
    """Unit tests for the conviction formula used in backtest_symbol.

    These tests call calculate_conviction() directly with the regime_aligned
    logic introduced by the fix, verifying parity with the live signal_log
    formula.
    """

    def test_regime_aligned_long_gets_bonus(self):
        """BULLISH bias + is_long=True → regime_aligned=True → +20 bonus."""
        btc_bias = "BULLISH"
        is_long = True
        regime_aligned = (btc_bias == "BULLISH" and is_long) or (btc_bias == "BEARISH" and not is_long)
        conviction = calculate_conviction(
            confidence=50,
            regime_aligned=regime_aligned,
            is_market_signal=False,  # LIMIT signal
        )
        # int((50/100)*60 + 20 + 0) = 50
        assert conviction == 50

    def test_regime_aligned_short_gets_bonus(self):
        """BEARISH bias + is_short=True → regime_aligned=True → +20 bonus."""
        btc_bias = "BEARISH"
        is_short = True
        regime_aligned = (btc_bias == "BULLISH" and not is_short) or (btc_bias == "BEARISH" and is_short)
        conviction = calculate_conviction(
            confidence=50,
            regime_aligned=regime_aligned,
            is_market_signal=False,  # LIMIT signal
        )
        # int((50/100)*60 + 20 + 0) = 50
        assert conviction == 50

    def test_regime_misaligned_no_bonus(self):
        """BEARISH bias + is_long=True → regime_aligned=False → no bonus."""
        btc_bias = "BEARISH"
        is_long = True
        regime_aligned = (btc_bias == "BULLISH" and is_long) or (btc_bias == "BEARISH" and not is_long)
        conviction = calculate_conviction(
            confidence=50,
            regime_aligned=regime_aligned,
            is_market_signal=False,  # LIMIT signal
        )
        # int((50/100)*60) = 30
        assert conviction == 30

    def test_neutral_regime_no_bonus(self):
        """NEUTRAL bias → regime_aligned=False regardless of direction → no bonus."""
        btc_bias = "NEUTRAL"
        is_long = True
        regime_aligned = (btc_bias == "BULLISH" and is_long) or (btc_bias == "BEARISH" and not is_long)
        conviction = calculate_conviction(
            confidence=50,
            regime_aligned=regime_aligned,
            is_market_signal=False,  # LIMIT signal
        )
        # int((50/100)*60) = 30
        assert conviction == 30

    def test_market_signal_bonus_stacks(self):
        """BULLISH + is_long + MARKET signal → both bonuses apply (+20 +10)."""
        btc_bias = "BULLISH"
        is_long = True
        regime_aligned = (btc_bias == "BULLISH" and is_long) or (btc_bias == "BEARISH" and not is_long)
        conviction = calculate_conviction(
            confidence=50,
            regime_aligned=regime_aligned,
            is_market_signal=True,  # "BUY" market signal
        )
        # int((50/100)*60 + 20 + 10) = 60
        assert conviction == 60
