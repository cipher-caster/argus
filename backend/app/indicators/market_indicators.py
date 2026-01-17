"""
Market-Level Indicators Module
Dashboard metrics computed from market data (separate from chart indicators)
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import pandas as pd
import numpy as np
import pandas_ta as ta


class IndicatorValue(BaseModel):
    """Single indicator metric for dashboard display"""
    value: float
    label: str
    timestamp: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    history: List[float] = []  # Sparkline data


class MarketIndicators(BaseModel):
    """All dashboard indicators"""
    btc_volatility: Optional[IndicatorValue] = None
    market_adx: Optional[IndicatorValue] = None
    total_market_cap: Optional[Dict[str, Any]] = None
    btc_dominance: Optional[IndicatorValue] = None


def calculate_volatility(closes: List[float], period: int = 14) -> IndicatorValue:
    """
    Calculate BTC volatility from closing prices.
    Uses standard deviation of daily returns, annualized and scaled to 1-100.
    
    Args:
        closes: List of closing prices (newest last)
        period: Lookback period for volatility calculation
    
    Returns:
        IndicatorValue with volatility score 1-100
    """
    if len(closes) < period + 1:
        return IndicatorValue(value=0, label="N/A", history=[])
    
    df = pd.DataFrame({'close': closes})
    
    # Calculate daily returns
    df['returns'] = df['close'].pct_change()
    
    # Rolling volatility (std of returns)
    df['volatility'] = df['returns'].rolling(window=period).std()
    
    # Annualize and scale to rough 1-100 range
    # Typical crypto volatility: 0.02-0.08 daily std -> annualized 30-150%
    latest_vol = df['volatility'].iloc[-1]
    annualized = latest_vol * np.sqrt(365) * 100 if not np.isnan(latest_vol) else 0
    
    # Scale to 1-100 (assuming 0-200% annualized maps to 1-100)
    scaled = max(1, min(100, annualized / 2))
    
    # Determine label
    if scaled < 25:
        label = "Low Vol"
    elif scaled < 50:
        label = "Medium"
    elif scaled < 75:
        label = "High"
    else:
        label = "Extreme"
    
    # History for sparkline (last 14 days of volatility)
    history = df['volatility'].dropna().tail(period).tolist()
    # Scale history too
    history = [max(1, min(100, v * np.sqrt(365) * 100 / 2)) if not np.isnan(v) else 0 for v in history]
    
    min_val = min(history) if history else 1
    max_val = max(history) if history else 100
    
    return IndicatorValue(
        value=round(scaled, 1),
        label=label,
        min_value=round(min_val, 1),
        max_value=round(max_val, 1),
        history=history
    )


def calculate_adx(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> IndicatorValue:
    """
    Calculate ADX (Average Directional Index) for trend strength.
    
    Args:
        highs: List of high prices
        lows: List of low prices
        closes: List of closing prices
        period: ADX period (default 14)
    
    Returns:
        IndicatorValue with ADX score 0-100
    """
    if len(closes) < period * 2:
        return IndicatorValue(value=0, label="N/A", history=[])
    
    df = pd.DataFrame({
        'high': highs,
        'low': lows,
        'close': closes
    })
    
    # Calculate ADX using pandas_ta
    adx_data = ta.adx(df['high'], df['low'], df['close'], length=period)
    
    if adx_data is None or adx_data.empty:
        return IndicatorValue(value=0, label="N/A", history=[])
    
    # ADX column name varies, find it
    adx_col = [c for c in adx_data.columns if 'ADX' in c and 'DM' not in c][0]
    
    latest_adx = adx_data[adx_col].iloc[-1]
    if np.isnan(latest_adx):
        latest_adx = 0
    
    # ADX interpretation:
    # < 20: Ranging/No trend
    # 20-40: Trending
    # 40-60: Strong trend
    # > 60: Very strong trend
    if latest_adx < 20:
        label = "Ranging"
    elif latest_adx < 40:
        label = "Trending"
    elif latest_adx < 60:
        label = "Strong"
    else:
        label = "V. Strong"
    
    # History for sparkline
    history = adx_data[adx_col].dropna().tail(period).tolist()
    history = [round(v, 1) if not np.isnan(v) else 0 for v in history]
    
    min_val = min(history) if history else 0
    max_val = max(history) if history else 100
    
    return IndicatorValue(
        value=round(latest_adx, 1),
        label=label,
        min_value=round(min_val, 1),
        max_value=round(max_val, 1),
        history=history
    )


def calculate_market_cap_stats(coins: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate total market cap (or volume) and market regime.
    Prioritizes 'market_cap' if available, falls back to 'volume_24h'.
    
    Args:
        coins: List of coin dicts
    
    Returns:
        Dict with total value, regime, and changes
    """
    if not coins:
        return {
            "value": 0,
            "change_1d": 0,
            "regime": "NEUTRAL",
            "regime_detail": "No Data",
            "min_value": 0,
            "max_value": 0,
            "history": []
        }
    
    # Check if we have valid market cap data (heuristic: check first few)
    has_mcap = any(c.get('market_cap', 0) and c.get('market_cap', 0) > 0 for c in coins[:5])
    value_key = 'market_cap' if has_mcap else 'volume_24h'
    
    # Sum values
    total_value = sum(c.get(value_key, 0) or 0 for c in coins)
    
    # Calculate average change (market sentiment)
    changes = [c.get('change_24h', 0) or 0 for c in coins if c.get('change_24h') is not None]
    avg_change = sum(changes) / len(changes) if changes else 0
    
    # Determine regime based on average change
    if avg_change > 2:
        regime = "BULLISH"
    elif avg_change < -2:
        regime = "BEARISH"
    else:
        regime = "NEUTRAL"
    
    # Count green vs red
    green_count = sum(1 for c in changes if c > 0)
    total_count = len(changes)
    green_pct = (green_count / total_count * 100) if total_count > 0 else 50
    
    return {
        "value": total_value,
        "metric_type": value_key,
        "change_1d": round(avg_change, 2),
        "regime": regime,
        "regime_detail": f"{int(green_pct)}% up",
        "min_value": total_value * 0.9, # Tighter bounds for MC
        "max_value": total_value * 1.1,
        "history": []
    }


def calculate_btc_dominance(coins: List[Dict[str, Any]]) -> IndicatorValue:
    """
    Calculate BTC Dominance (BTC Value / Total Value).
    Prioritizes 'market_cap', falls back to 'volume_24h'.
    
    Args:
        coins: List of coin dicts
    
    Returns:
        IndicatorValue with dominance percentage
    """
    if not coins:
        return IndicatorValue(value=0, label="N/A", history=[])
    
    # Check if we have valid market cap data
    has_mcap = any(c.get('market_cap', 0) and c.get('market_cap', 0) > 0 for c in coins[:5])
    value_key = 'market_cap' if has_mcap else 'volume_24h'
    
    total_value = sum(c.get(value_key, 0) or 0 for c in coins)
    
    # Find BTC value
    btc_value = 0
    for c in coins:
        symbol = c.get('symbol', '').upper()
        # Handle various BTC symbol formats
        if symbol in ('BTC/USDT', 'BTCUSDT', 'BTC', 'BITCOIN'):
            btc_value = c.get(value_key, 0) or 0
            break
    
    if total_value == 0:
        return IndicatorValue(value=0, label="N/A", history=[])
    
    dominance = (btc_value / total_value) * 100
    
    # Label based on dominance level (Standard MC Dom levels)
    if dominance > 60:
        label = "Maximalist"
    elif dominance > 50:
        label = "High"
    elif dominance > 40:
        label = "Normal"
    else:
        label = "Alt Season"
    
    return IndicatorValue(
        value=round(dominance, 1),
        label=label,
        min_value=30, # Historical bounds ~35%
        max_value=70, # Historical bounds ~70%
        history=[]
    )
