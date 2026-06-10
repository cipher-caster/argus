"""
Tests for Indicator Calculator.
"""

import pandas as pd
import pytest

from app.indicators.calculator import (
    INDICATOR_REGISTRY,
    calculate_indicator,
    get_available_indicators,
)


@pytest.fixture
def mock_df():
    """Returns a simple continuous dataframe of 100 rows."""
    timestamps = pd.date_range("2024-01-01", periods=100, freq="1D")
    # Convert to integer milliseconds representing Unix epoch
    ts_ints = timestamps.astype("int64") // 10**6
    import numpy as np

    np.random.seed(42)
    prices = np.linspace(100, 200, 100) + np.random.normal(0, 1, 100)

    return pd.DataFrame(
        {
            "timestamp": ts_ints,
            "open": prices,
            "high": prices * 1.05,
            "low": prices * 0.95,
            "close": prices,
            "volume": np.random.randint(1000, 5000, 100),
        }
    )


def test_get_available_indicators():
    """Ensure the registry correctly outputs definitions."""
    indicators = get_available_indicators()
    assert len(indicators) == len(INDICATOR_REGISTRY)
    for ind in indicators:
        assert hasattr(ind, "name")
        assert hasattr(ind, "type")
        assert ind.type in ("overlay", "pane")


def test_calculate_unknown_indicator(mock_df):
    """Unknown indicators should return None."""
    result = calculate_indicator(mock_df, "made_up_magic_indicator", {})
    assert result is None


def test_calculate_ema(mock_df):
    """Test EMA calculation produces expected data shape."""
    result = calculate_indicator(mock_df, "ema", {"length": 10})
    assert result is not None
    assert result.name == "ema"
    assert result.type == "overlay"

    # 10 length EMA on 100 items will have ~90 non-null values
    assert len(result.data) > 80
    assert "timestamp" in result.data[0]
    assert "value" in result.data[0]


def test_calculate_macd_returns_multiple_components(mock_df):
    """MACD should return macd line, signal line, and histogram."""
    result = calculate_indicator(mock_df, "macd", {"fast": 12, "slow": 26, "signal": 9})
    assert result is not None
    assert len(result.data) > 50
    first_valid = result.data[0]
    assert "macd" in first_valid
    assert "signal" in first_valid
    assert "histogram" in first_valid


def test_calculate_bbands_returns_bands(mock_df):
    """Bollinger Bands should return upper, middle, and lower bands."""
    result = calculate_indicator(mock_df, "bbands", {"length": 20, "std": 2.0})
    assert result is not None
    assert len(result.data) > 70
    first_valid = result.data[0]
    assert "upper" in first_valid
    assert "middle" in first_valid
    assert "lower" in first_valid


def test_calculate_auto_fib(mock_df):
    """Auto Fib returns multiple retracement levels."""
    result = calculate_indicator(mock_df, "auto_fib", {"lookback": 50})
    assert result is not None
    assert len(result.data) > 40
    first_valid = result.data[-1]  # Check newest
    assert "top" in first_valid
    assert "bottom" in first_valid
    assert "fib_0_618" in first_valid
