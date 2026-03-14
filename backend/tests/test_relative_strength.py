"""
Tests for Relative Strength indicator.
"""
import pytest
import pandas as pd
from app.indicators.relative_strength import calculate_relative_strength

def test_relative_strength_empty_df():
    """Returns neutral 0.0 metrics if either dataframe is empty."""
    res1 = calculate_relative_strength(pd.DataFrame(), pd.DataFrame())
    res2 = calculate_relative_strength(pd.DataFrame({"close": [1]}), pd.DataFrame())
    
    assert res1["strength"] == "NEUTRAL"
    assert res2["strength"] == "NEUTRAL"
    assert res2["performance_relative_pct"] == 0.0

def test_relative_strength_neutral():
    """Test when Altcoin and BTC move roughly the same."""
    # Both start at 100, both go to 105
    ts = pd.date_range("2024-01-01", periods=10, freq="1h")
    alt = pd.DataFrame({"timestamp": ts, "close": range(100, 110)})
    btc = pd.DataFrame({"timestamp": ts, "close": range(100, 110)})
    
    res = calculate_relative_strength(alt, btc)
    
    assert res["strength"] == "NEUTRAL"
    assert res["performance_relative_pct"] == 0.0
    assert res["current_ratio"] == 1.0


def test_relative_strength_outperforming():
    """Test when Altcoin gains significantly more than BTC."""
    ts = pd.date_range("2024-01-01", periods=10, freq="1h")
    # alt starts 100 goes to 120
    alt = pd.DataFrame({"timestamp": ts, "close": range(100, 120, 2)})
    # btc starts 100 goes to 105 (slower growth)
    btc = pd.DataFrame({"timestamp": ts, "close": [100 + i*0.5 for i in range(10)]})
    
    res = calculate_relative_strength(alt, btc)
    
    assert res["strength"] == "OUTPERFORMING"
    assert res["performance_relative_pct"] > 0
    assert res["current_ratio"] > 1.0

def test_relative_strength_underperforming():
    """Test when Altcoin drops while BTC stays flat."""
    ts = pd.date_range("2024-01-01", periods=10, freq="1h")
    # alt drops 100 to 50
    alt = pd.DataFrame({"timestamp": ts, "close": [100 - i*5 for i in range(10)]})
    # btc flat at 100
    btc = pd.DataFrame({"timestamp": ts, "close": [100 for i in range(10)]})
    
    res = calculate_relative_strength(alt, btc)
    
    assert res["strength"] == "UNDERPERFORMING"
    assert res["performance_relative_pct"] < 0
    assert res["current_ratio"] < 1.0
