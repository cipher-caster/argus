"""
Unit tests for TitanStrategy.
Tests signal validity, confidence range, insufficient data handling, and directional logic.
"""

import numpy as np
import pandas as pd
from conftest import make_bearish_ohlcv, make_bullish_ohlcv, make_ohlcv

from app.strategies.titan import TitanStrategy

titan = TitanStrategy()

VALID_SIGNALS = {"BUY", "SELL", "BUY_LIMIT", "SELL_LIMIT", "WAIT_OB", "WAIT_OS", "NEUTRAL"}


# ---------------------------------------------------------------------------
# Insufficient data
# ---------------------------------------------------------------------------


class TestInsufficientData:
    def test_empty_df_returns_error(self):
        result = titan.analyze(pd.DataFrame())
        assert "error" in result

    def test_fewer_than_200_candles_returns_error(self):
        df = make_ohlcv(199)
        result = titan.analyze(df)
        assert "error" in result

    def test_exactly_200_candles_does_not_return_error(self):
        # Titan requires >= 200 (len(df) < 200 check in source)
        df = make_ohlcv(200)
        result = titan.analyze(df)
        assert "error" not in result

    def test_201_candles_does_not_return_error(self):
        df = make_ohlcv(201)
        result = titan.analyze(df)
        assert "error" not in result


# ---------------------------------------------------------------------------
# Output shape and validity
# ---------------------------------------------------------------------------


class TestOutputShape:
    def test_analyze_returns_required_keys(self):
        df = make_ohlcv(250)
        result = titan.analyze(df)
        assert "error" not in result
        for key in ("signal", "confidence", "trend", "momentum", "volatility", "targets", "sizing"):
            assert key in result, f"Missing key: {key}"

    def test_signal_is_valid_enum(self):
        for trend in ("up", "down"):
            df = make_ohlcv(250, trend=trend)
            result = titan.analyze(df)
            if "error" not in result:
                assert result["signal"] in VALID_SIGNALS, f"Unexpected signal: {result['signal']}"

    def test_confidence_in_range(self):
        for trend in ("up", "down"):
            df = make_ohlcv(250, trend=trend)
            result = titan.analyze(df)
            if "error" not in result:
                assert 0 <= result["confidence"] <= 100

    def test_trend_is_valid(self):
        df = make_ohlcv(250)
        result = titan.analyze(df)
        if "error" not in result:
            assert result["trend"] in ("BULLISH", "BEARISH")

    def test_targets_has_entry_tp_sl(self):
        df = make_ohlcv(250)
        result = titan.analyze(df)
        if "error" not in result:
            targets = result["targets"]
            assert "entry" in targets
            assert "tp" in targets
            assert "sl" in targets

    def test_momentum_has_required_keys(self):
        df = make_ohlcv(250)
        result = titan.analyze(df)
        if "error" not in result:
            mom = result["momentum"]
            for key in ("status", "rsi_val", "is_overbought", "is_oversold"):
                assert key in mom

    def test_sizing_is_string(self):
        df = make_ohlcv(250)
        result = titan.analyze(df)
        if "error" not in result:
            assert isinstance(result["sizing"], str)


# ---------------------------------------------------------------------------
# Confidence levels per signal type
# ---------------------------------------------------------------------------


class TestConfidenceLevels:
    def test_wait_signals_have_zero_confidence(self):
        # Run many seeds and check any WAIT signal always has 0 confidence
        for seed in range(20):
            np.random.seed(seed)
            df = make_ohlcv(250)
            result = titan.analyze(df)
            if "error" not in result and result["signal"] in ("WAIT_OB", "WAIT_OS"):
                assert result["confidence"] == 0, (
                    f"WAIT signal should have 0 confidence, got {result['confidence']}"
                )

    def test_buy_sell_signals_have_80_confidence(self):
        for seed in range(30):
            np.random.seed(seed)
            df = make_ohlcv(250)
            result = titan.analyze(df)
            if "error" not in result and result["signal"] in ("BUY", "SELL"):
                assert result["confidence"] == 80

    def test_limit_signals_have_60_confidence(self):
        for seed in range(30):
            np.random.seed(seed)
            df = make_ohlcv(250)
            result = titan.analyze(df)
            if "error" not in result and result["signal"] in ("BUY_LIMIT", "SELL_LIMIT"):
                assert result["confidence"] == 60


# ---------------------------------------------------------------------------
# Directional logic
# ---------------------------------------------------------------------------


class TestDirectionalLogic:
    def test_bullish_trend_produces_no_sell_signal(self):
        df = make_bullish_ohlcv()
        result = titan.analyze(df)
        if "error" not in result:
            assert result["signal"] not in ("SELL", "SELL_LIMIT", "WAIT_OS"), (
                f"Bullish trend should not produce {result['signal']}"
            )

    def test_bearish_trend_produces_no_buy_signal(self):
        df = make_bearish_ohlcv()
        result = titan.analyze(df)
        if "error" not in result:
            assert result["signal"] not in ("BUY", "BUY_LIMIT", "WAIT_OB"), (
                f"Bearish trend should not produce {result['signal']}"
            )

    def test_buy_signal_requires_bullish_trend(self):
        # If we get a BUY or BUY_LIMIT, trend must be BULLISH
        for seed in range(50):
            np.random.seed(seed)
            df = make_ohlcv(250)
            result = titan.analyze(df)
            if "error" not in result and result["signal"] in ("BUY", "BUY_LIMIT"):
                assert result["trend"] == "BULLISH"

    def test_sell_signal_requires_bearish_trend(self):
        for seed in range(50):
            np.random.seed(seed)
            df = make_ohlcv(250)
            result = titan.analyze(df)
            if "error" not in result and result["signal"] in ("SELL", "SELL_LIMIT"):
                assert result["trend"] == "BEARISH"

    def test_long_sl_below_entry(self):
        df = make_bullish_ohlcv()
        result = titan.analyze(df)
        if "error" not in result and result["signal"] in ("BUY", "BUY_LIMIT"):
            targets = result["targets"]
            assert targets["sl"] < targets["entry"]

    def test_long_tp_above_entry(self):
        df = make_bullish_ohlcv()
        result = titan.analyze(df)
        if "error" not in result and result["signal"] in ("BUY", "BUY_LIMIT"):
            targets = result["targets"]
            assert targets["tp"] > targets["entry"]

    def test_short_sl_above_entry(self):
        df = make_bearish_ohlcv()
        result = titan.analyze(df)
        if "error" not in result and result["signal"] in ("SELL", "SELL_LIMIT"):
            targets = result["targets"]
            assert targets["sl"] > targets["entry"]

    def test_short_tp_below_entry(self):
        df = make_bearish_ohlcv()
        result = titan.analyze(df)
        if "error" not in result and result["signal"] in ("SELL", "SELL_LIMIT"):
            targets = result["targets"]
            assert targets["tp"] < targets["entry"]
