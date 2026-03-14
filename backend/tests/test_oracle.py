"""
Unit tests for OracleStrategy.
Tests score bounds, voter logic, signal synthesis, and backtest stats.
"""
import pytest
import numpy as np
import pandas as pd
from app.strategies.oracle import OracleStrategy
from conftest import make_ohlcv

oracle = OracleStrategy()




def make_row(**kwargs) -> pd.Series:
    """Build a minimal indicator row for _calculate_earnest_score tests."""
    defaults = {
        "close": 100.0,
        "rsi": 55.0,
        "bb_upper": 110.0,
        "bb_lower": 90.0,
        "bb_mid": 100.0,
        "adx": 25.0,
        "ema200": 95.0,
        "atr": 1.5,
    }
    defaults.update(kwargs)
    return pd.Series(defaults)


# ---------------------------------------------------------------------------
# _calculate_earnest_score — voter unit tests
# ---------------------------------------------------------------------------

class TestEarnestVoters:
    def test_all_bullish_gives_plus_four(self):
        # RSI in (50,70): +1, BB pos > 0.1: +1, ADX > 20 & close > ema: +1, EMA close > ema: +1
        row = make_row(rsi=60, close=108, bb_upper=110, bb_lower=90, bb_mid=100, adx=30, ema200=95)
        result = oracle._calculate_earnest_score(row)
        assert result["score"] == 4
        assert all(v == 1 for v in result["voters"].values())

    def test_all_bearish_gives_minus_four(self):
        # RSI in (30,50): -1, BB pos < -0.1: -1, ADX > 20 & close < ema: -1, EMA close < ema: -1
        row = make_row(rsi=40, close=88, bb_upper=110, bb_lower=90, bb_mid=100, adx=30, ema200=95)
        result = oracle._calculate_earnest_score(row)
        assert result["score"] == -4
        assert all(v == -1 for v in result["voters"].values())

    def test_score_always_in_bounds(self):
        for _ in range(50):
            rsi = np.random.uniform(0, 100)
            close = np.random.uniform(50, 150)
            row = make_row(rsi=rsi, close=close, adx=np.random.uniform(0, 50))
            result = oracle._calculate_earnest_score(row)
            assert -4 <= result["score"] <= 4

    def test_rsi_above_70_gives_zero(self):
        row = make_row(rsi=75, close=108, bb_upper=110, bb_lower=90, bb_mid=100, adx=30, ema200=95)
        voters = oracle._calculate_earnest_score(row)["voters"]
        assert voters["rsi"] == 0

    def test_rsi_below_30_gives_zero(self):
        row = make_row(rsi=25, close=88, bb_upper=110, bb_lower=90, bb_mid=100, adx=30, ema200=95)
        voters = oracle._calculate_earnest_score(row)["voters"]
        assert voters["rsi"] == 0

    def test_adx_below_limit_gives_zero_adx_vote(self):
        # ADX below 20 means no ADX vote regardless of EMA
        row = make_row(rsi=60, close=108, adx=15, ema200=95)
        voters = oracle._calculate_earnest_score(row)["voters"]
        assert voters["adx"] == 0

    def test_nan_rsi_gives_zero_voter(self):
        row = make_row(rsi=float("nan"))
        voters = oracle._calculate_earnest_score(row)["voters"]
        assert voters["rsi"] == 0

    def test_nan_ema_gives_zero_ema_and_adx_votes(self):
        row = make_row(ema200=float("nan"))
        voters = oracle._calculate_earnest_score(row)["voters"]
        assert voters["ema"] == 0
        assert voters["adx"] == 0

    def test_flat_bb_gives_zero_bb_vote(self):
        row = make_row(bb_upper=100, bb_lower=100, bb_mid=100)
        voters = oracle._calculate_earnest_score(row)["voters"]
        assert voters["bb"] == 0

    def test_voters_dict_has_four_keys(self):
        result = oracle._calculate_earnest_score(make_row())
        assert set(result["voters"].keys()) == {"rsi", "bb", "adx", "ema"}


# ---------------------------------------------------------------------------
# _synthesize_signal
# ---------------------------------------------------------------------------

class TestSynthesizeSignal:
    def test_strong_buy_requires_macro_ge2_and_earnest_ge3(self):
        assert oracle._synthesize_signal(3, 2) == "STRONG_BUY"
        assert oracle._synthesize_signal(4, 3) == "STRONG_BUY"

    def test_buy_when_earnest_ge3_but_macro_lt2(self):
        assert oracle._synthesize_signal(3, 1) == "BUY"
        assert oracle._synthesize_signal(4, 0) == "BUY"

    def test_strong_sell_requires_macro_0_and_earnest_le_minus3(self):
        assert oracle._synthesize_signal(-3, 0) == "STRONG_SELL"
        assert oracle._synthesize_signal(-4, 0) == "STRONG_SELL"

    def test_sell_when_earnest_le_minus3_but_macro_nonzero(self):
        assert oracle._synthesize_signal(-3, 1) == "SELL"
        assert oracle._synthesize_signal(-4, 2) == "SELL"

    def test_neutral_for_mid_range_scores(self):
        for earnest in range(-2, 3):
            assert oracle._synthesize_signal(earnest, 1) == "NEUTRAL"

    def test_boundary_earnest_2_is_neutral(self):
        assert oracle._synthesize_signal(2, 3) == "NEUTRAL"
        assert oracle._synthesize_signal(-2, 0) == "NEUTRAL"


# ---------------------------------------------------------------------------
# analyze() — integration with real indicator computation
# ---------------------------------------------------------------------------

class TestOracleAnalyze:
    def test_empty_df_returns_error(self):
        result = oracle.analyze(pd.DataFrame(), pd.DataFrame())
        assert "error" in result

    def test_analyze_returns_required_keys(self):
        df = make_ohlcv(300, trend="up")
        result = oracle.analyze(df, df)
        assert "error" not in result
        for key in ("signal", "confidence", "bias", "state", "earnest", "macro", "targets", "advice", "performance"):
            assert key in result, f"Missing key: {key}"

    def test_earnest_score_in_bounds(self):
        for trend in ("up", "down"):
            df = make_ohlcv(300, trend=trend)
            result = oracle.analyze(df, df)
            if "error" not in result:
                assert -4 <= result["earnest"]["score"] <= 4

    def test_signal_is_valid_string(self):
        valid = {"STRONG_BUY", "BUY", "STRONG_SELL", "SELL", "NEUTRAL"}
        df = make_ohlcv(300, trend="up")
        result = oracle.analyze(df, df)
        if "error" not in result:
            assert result["signal"] in valid

    def test_bias_is_valid(self):
        df = make_ohlcv(300, trend="up")
        result = oracle.analyze(df, df)
        if "error" not in result:
            assert result["bias"] in ("BULLISH", "BEARISH", "NEUTRAL")

    def test_state_is_valid(self):
        df = make_ohlcv(300, trend="up")
        result = oracle.analyze(df, df)
        if "error" not in result:
            assert result["state"] in ("SLEEPING", "TRENDING", "SUPER TREND")

    def test_performance_has_required_fields(self):
        df = make_ohlcv(300, trend="up")
        result = oracle.analyze(df, df)
        if "error" not in result:
            perf = result["performance"]
            assert "total_trades" in perf
            assert "win_rate" in perf
            assert "net_profit" in perf
            assert isinstance(perf["total_trades"], int)
            assert 0.0 <= perf["win_rate"] <= 100.0

    def test_confidence_format(self):
        df = make_ohlcv(300, trend="up")
        result = oracle.analyze(df, df)
        if "error" not in result:
            # confidence is returned as "{n}/4"
            conf = result["confidence"]
            assert "/" in str(conf)
            n = int(str(conf).split("/")[0])
            assert 0 <= n <= 4
