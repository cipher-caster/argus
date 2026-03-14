"""
Tests for Market Level Indicators (Dashboard metrics).
"""
import pytest
from app.indicators.market_indicators import (
    calculate_volatility,
    calculate_adx,
    calculate_market_cap_stats,
    calculate_btc_dominance,
    calculate_average_rsi
)


def test_calculate_volatility_insufficient_data():
    """Returns empty/zeroized data if not enough closes."""
    result = calculate_volatility([50000, 51000]) # period is 14 by default
    assert result.value == 0
    assert result.label == "N/A"
    assert len(result.history) == 0


def test_calculate_volatility_success():
    """Calculates volatility scaled 1-100."""
    import numpy as np
    np.random.seed(42)
    closes = np.linspace(50000, 60000, 30) + np.random.normal(0, 1000, 30)
    result = calculate_volatility(closes.tolist())
    
    assert result.value > 0
    assert result.value <= 100
    assert result.label in ["Low Vol", "Medium", "High", "Extreme"]
    assert len(result.history) == 14  # Default period


def test_calculate_adx_success():
    """Calculates ADX trend strength."""
    # Create an obvious uptrend
    highs = [10+i for i in range(40)]
    lows = [8+i for i in range(40)]
    closes = [9+i for i in range(40)]
    
    result = calculate_adx(highs, lows, closes)
    
    assert result.value > 0
    assert result.label in ["Ranging", "Trending", "Strong", "V. Strong"]


def test_calculate_market_cap_stats():
    """Calculates total mcap and regime from coin list."""
    coins = [
        {"symbol": "BTC/USDT", "market_cap": 1000, "change_24h": 5.0, "sparkline_in_7d": [900, 950, 1000], "price": 10},
        {"symbol": "ETH/USDT", "market_cap": 500, "change_24h": -1.0, "sparkline_in_7d": [550, 520, 500], "price": 5}
    ]
    
    stats = calculate_market_cap_stats(coins)
    
    assert stats["value"] == 1500
    assert stats["metric_type"] == "market_cap"
    assert stats["change_1d"] == 2.0  # Average of 5 and -1
    # Average change of 2.0 is NEUTRAL in calculate_market_cap_stats (> 2 is BULLISH)
    assert stats["regime"] == "NEUTRAL"
    assert len(stats["history"]) == 3


def test_calculate_btc_dominance():
    """Calculates BTC dominance."""
    coins = [
        {"symbol": "BTC/USDT", "market_cap": 600, "sparkline_in_7d": [500, 550, 600], "price": 10},
        {"symbol": "ETH/USDT", "market_cap": 400, "sparkline_in_7d": [500, 450, 400], "price": 5}
    ]
    
    result = calculate_btc_dominance(coins)
    
    assert result.value == 60.0  # 600 / (600 + 400)
    assert result.label == "High" # 60.0 is not > 60, it falls into > 50
    

def test_calculate_average_rsi():
    """Calculates average RSI from sparklines."""
    coins = [
        {"symbol": "BTC", "sparkline_in_7d": [100 + i for i in range(200)]}, # Uptrend
        {"symbol": "ETH", "sparkline_in_7d": [100 + i*0.5 for i in range(200)]} # Uptrend
    ]
    
    result = calculate_average_rsi(coins, period=14)
    # Should be high RSI since both are strictly uptrending
    assert result.value > 50
    assert len(result.history) > 0
