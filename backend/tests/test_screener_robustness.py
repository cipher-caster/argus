import pytest
import pandas as pd
import numpy as np
from app.indicators.screener import run_oracle_screener

def test_screener_handles_nan_indicators():
    """Verify that run_oracle_screener handles DataFrames with NaN indicators gracefully."""
    
    # Create a DataFrame with NaNs for long-term indicators (simulating new asset)
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=300),
        "open": [100.0] * 300,
        "high": [110.0] * 300,
        "low": [90.0] * 300,
        "close": [105.0] * 300,
        "volume": [1000.0] * 300
    })
    
    # ...
    
    df_data = {"NEWCOIN/USDT": df}
    btc_df = pd.DataFrame() # Empty BTC df
    
    try:
        results = run_oracle_screener(df_data, btc_df)
        # Should complete without raising: '>' not supported between instances of 'float' and 'NoneType'
        assert len(results) >= 0
        # For a new coin with all NaNs, score should be low/neutral, might be filtered.
        # But should NOT crash.
    except Exception as e:
        pytest.fail(f"run_oracle_screener crashed with NaNs: {e}")

def test_screener_handles_empty_btc_macro():
    """Verify screener handles scenario with no BTC data for relative strength."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=300),
        "open": [100.0] * 300,
        "high": [110.0] * 300,
        "low": [90.0] * 300,
        "close": [105.0] * 300,
        "volume": [1000.0] * 300
    })
    
    df_data = {"BTC/USDT": df}
    results = run_oracle_screener(df_data, pd.DataFrame())
    # BTC/USDT with constant price 105 will have:
    # EMA200=100 (after ~200 bars), Close=105 -> +1 EMA voter
    # RSI ~ 100? or 50 if flat? flat price -> RSI=50.
    # Score might be 1 or 2. 
    # If filtered, that's fine as long as no crash.
    assert isinstance(results, list)

