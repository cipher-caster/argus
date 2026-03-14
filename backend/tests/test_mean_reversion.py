"""
Tests for Mean Reversion indicator.
"""
import pytest
import pandas as pd
import numpy as np
from app.indicators.mean_reversion import detect_mean_reversion


def test_detect_mean_reversion_insufficient_data():
    """Ensure it handles empty or short DataFrames gracefully."""
    empty_df = pd.DataFrame()
    short_df = pd.DataFrame({"close": [1, 2, 3]})
    
    res1 = detect_mean_reversion(empty_df)
    res2 = detect_mean_reversion(short_df)
    
    assert res1["opportunity"] == "NONE"
    assert res1["is_extended"] is False
    assert res2["opportunity"] == "NONE"


def test_detect_mean_reversion_not_extended():
    """Test normal price action near the mean returns NONE."""
    # Create 250 candles moving sideways
    close = np.linspace(100, 100, 250)
    high = close + 2
    low = close - 2
    df = pd.DataFrame({"close": close, "high": high, "low": low})
    
    res = detect_mean_reversion(df)
    
    assert res["is_extended"] is False
    assert res["opportunity"] == "NONE"
    assert res["extension_atr"] < 1.0


def test_detect_mean_reversion_spot_buy():
    """Test downside overextension returns SPOT_BUY."""
    # 250 candles: first 240 at 100, last 10 dump to 50
    close = np.concatenate([np.linspace(100, 100, 240), np.linspace(100, 50, 10)])
    high = close + 2
    low = close - 2
    df = pd.DataFrame({"close": close, "high": high, "low": low})
    
    res = detect_mean_reversion(df, atr_mult=2.0)
    
    assert res["is_extended"] is True
    assert res["opportunity"] == "SPOT_BUY"
    assert res["price"] == 50.0
    assert res["target"] > 90.0  # Mean should still be high


def test_detect_mean_reversion_sell():
    """Test upside overextension returns DE-RISK_LONG."""
    # 250 candles: first 240 at 100, last 10 pump to 150
    close = np.concatenate([np.linspace(100, 100, 240), np.linspace(100, 150, 10)])
    high = close + 2
    low = close - 2
    df = pd.DataFrame({"close": close, "high": high, "low": low})
    
    res = detect_mean_reversion(df, atr_mult=2.0)
    
    assert res["is_extended"] is True
    assert res["opportunity"] == "DE-RISK_LONG"
    assert res["price"] == 150.0
    assert res["target"] < 110.0  # Mean should be roughly lower
