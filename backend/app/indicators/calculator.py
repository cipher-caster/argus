"""
Indicator Calculator Module
Provides a registry of technical indicators with configurable parameters
"""

from typing import Dict, List, Any, Optional
import logging
from pydantic import BaseModel
import pandas as pd
import pandas_ta as ta

logger = logging.getLogger(__name__)


class IndicatorDefinition(BaseModel):
    """Definition of an available indicator"""
    name: str
    display_name: str
    type: str  # "overlay" or "pane"
    params: List[Dict[str, Any]]  # Parameter definitions with defaults
    description: str


class IndicatorResult(BaseModel):
    """Result of indicator calculation"""
    name: str
    type: str
    params: Dict[str, Any]
    data: List[Dict[str, Any]]  # [{timestamp, value, ...}]


# Indicator Registry - easily extensible
INDICATOR_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ema": {
        "display_name": "EMA",
        "type": "overlay",
        "params": [
            {"name": "length", "type": "int", "default": 20, "min": 1, "max": 500}
        ],
        "description": "Exponential Moving Average",
    },
    "sma": {
        "display_name": "SMA", 
        "type": "overlay",
        "params": [
            {"name": "length", "type": "int", "default": 20, "min": 1, "max": 500}
        ],
        "description": "Simple Moving Average",
    },
    "rsi": {
        "display_name": "RSI",
        "type": "pane",
        "params": [
            {"name": "length", "type": "int", "default": 14, "min": 2, "max": 100}
        ],
        "description": "Relative Strength Index",
    },
    "obv": {
        "display_name": "OBV",
        "type": "pane",
        "params": [],
        "description": "On Balance Volume",
    },
    "bbands": {
        "display_name": "Bollinger Bands",
        "type": "overlay",
        "params": [
            {"name": "length", "type": "int", "default": 20, "min": 5, "max": 200},
            {"name": "std", "type": "float", "default": 2.0, "min": 0.5, "max": 4.0}
        ],
        "description": "Bollinger Bands (Upper, Middle, Lower)",
    },
    "macd": {
        "display_name": "MACD",
        "type": "pane",
        "params": [
            {"name": "fast", "type": "int", "default": 12, "min": 2, "max": 100},
            {"name": "slow", "type": "int", "default": 26, "min": 2, "max": 200},
            {"name": "signal", "type": "int", "default": 9, "min": 2, "max": 50}
        ],
        "description": "Moving Average Convergence Divergence",
    },
    "linreg": {
        "display_name": "Linear Regression",
        "type": "overlay",
        "params": [
            {"name": "length", "type": "int", "default": 50, "min": 5, "max": 200}
        ],
        "description": "Linear Regression Curve (Moneyline)",
    },
    "atr": {
        "display_name": "ATR",
        "type": "pane",
        "params": [
            {"name": "length", "type": "int", "default": 14, "min": 1, "max": 100}
        ],
        "description": "Average True Range (Volatility)",
    },
    "supertrend": {
        "display_name": "SuperTrend",
        "type": "overlay",
        "params": [
            {"name": "length", "type": "int", "default": 10, "min": 1, "max": 100},
            {"name": "multiplier", "type": "float", "default": 3.0, "min": 1.0, "max": 10.0}
        ],
        "description": "SuperTrend Indicator",
    },
    "auto_fib": {
        "display_name": "Auto Fib",
        "type": "overlay",
        "params": [
            {"name": "lookback", "type": "int", "default": 200, "min": 50, "max": 500}
        ],
        "description": "Auto Fibonacci Retracement Levels",
    },
    "fvg": {
        "display_name": "Fair Value Gap",
        "type": "overlay",
        "params": [],
        "description": "Detects 3-candle Fair Value Gaps (ICT/SMC)",
    },
    "mss": {
        "display_name": "Market Structure Shift",
        "type": "overlay",
        "params": [
            {"name": "lookback", "type": "int", "default": 2, "min": 1, "max": 10}
        ],
        "description": "Detects Bullish/Bearish Market Structure Shifts (ICT/SMC)",
    },
    "sweep": {
        "display_name": "Liquidity Sweep",
        "type": "overlay",
        "params": [
            {"name": "lookback", "type": "int", "default": 24, "min": 5, "max": 200}
        ],
        "description": "Detects wicks beyond 24H high/low (ICT/SMC Liquidity Grab)",
    },
}


def get_available_indicators() -> List[IndicatorDefinition]:
    """Get list of all available indicators"""
    return [
        IndicatorDefinition(
            name=name,
            display_name=config["display_name"],
            type=config["type"],
            params=config["params"],
            description=config["description"]
        )
        for name, config in INDICATOR_REGISTRY.items()
    ]


def calculate_indicator(
    df: pd.DataFrame,
    indicator_name: str,
    params: Dict[str, Any]
) -> Optional[IndicatorResult]:
    """
    Calculate a single indicator on OHLCV data
    
    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        indicator_name: Name of indicator from registry
        params: Parameter values for the indicator
        
    Returns:
        IndicatorResult with calculated values
    """
    if indicator_name not in INDICATOR_REGISTRY:
        return None
    
    config = INDICATOR_REGISTRY[indicator_name]
    result_data = []
    
    try:
        if indicator_name == "ema":
            length = params.get("length", 20)
            values = ta.ema(df["close"], length=length)
            result_data = _series_to_list(df["timestamp"], values)
            
        elif indicator_name == "sma":
            length = params.get("length", 20)
            values = ta.sma(df["close"], length=length)
            result_data = _series_to_list(df["timestamp"], values)
            
        elif indicator_name == "rsi":
            length = params.get("length", 14)
            values = ta.rsi(df["close"], length=length)
            result_data = _series_to_list(df["timestamp"], values)
            
        elif indicator_name == "obv":
            values = ta.obv(df["close"], df["volume"])
            result_data = _series_to_list(df["timestamp"], values)
            
        elif indicator_name == "bbands":
            length = params.get("length", 20)
            std = params.get("std", 2.0)
            bbands = ta.bbands(df["close"], length=length, std=std)
            # Returns multiple columns: BBL, BBM, BBU, BBB, BBP
            result_data = _bbands_to_list(df["timestamp"], bbands)
            
        elif indicator_name == "macd":
            fast = params.get("fast", 12)
            slow = params.get("slow", 26)
            signal = params.get("signal", 9)
            macd_data = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
            result_data = _macd_to_list(df["timestamp"], macd_data)
            
        elif indicator_name == "linreg":
            length = params.get("length", 50)
            values = ta.linreg(df["close"], length=length)
            result_data = _series_to_list(df["timestamp"], values)

        elif indicator_name == "atr":
            length = params.get("length", 14)
            values = ta.atr(df["high"], df["low"], df["close"], length=length)
            result_data = _series_to_list(df["timestamp"], values)

        elif indicator_name == "supertrend":
            length = params.get("length", 10)
            multiplier = params.get("multiplier", 3.0)
            st = ta.supertrend(df["high"], df["low"], df["close"], length=length, multiplier=multiplier)
            result_data = _supertrend_to_list(df["timestamp"], st)

        elif indicator_name == "auto_fib":
            lookback = params.get("lookback", 200)
            result_data = _fib_to_list(df["timestamp"], df["high"], df["low"], lookback)

        elif indicator_name == "fvg":
            result_data = _fvg_to_list(df)

        elif indicator_name == "mss":
            lookback = params.get("lookback", 2)
            result_data = _mss_to_list(df, lookback)

        elif indicator_name == "sweep":
            lookback = params.get("lookback", 24)
            result_data = _sweep_to_list(df, lookback)
            
    except Exception as e:
        logger.error(f"Error calculating {indicator_name}: {e}")
        return None
    
    return IndicatorResult(
        name=indicator_name,
        type=config["type"],
        params=params,
        data=result_data
    )


def _series_to_list(timestamps: pd.Series, values: pd.Series) -> List[Dict[str, Any]]:
    """Convert pandas series to list of {timestamp, value} dicts"""
    result = []
    for ts, val in zip(timestamps, values):
        if pd.notna(val):
            result.append({"timestamp": int(ts), "value": float(val)})
    return result


def _bbands_to_list(timestamps: pd.Series, bbands: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert Bollinger Bands DataFrame to list"""
    result = []
    cols = bbands.columns.tolist()
    for i, ts in enumerate(timestamps):
        row = bbands.iloc[i]
        if pd.notna(row.iloc[0]):
            result.append({
                "timestamp": int(ts),
                "lower": float(row.iloc[0]),  # BBL
                "middle": float(row.iloc[1]),  # BBM
                "upper": float(row.iloc[2]),  # BBU
            })
    return result


def _macd_to_list(timestamps: pd.Series, macd: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert MACD DataFrame to list"""
    result = []
    for i, ts in enumerate(timestamps):
        row = macd.iloc[i]
        if pd.notna(row.iloc[0]):
            result.append({
                "timestamp": int(ts),
                "macd": float(row.iloc[0]),
                "signal": float(row.iloc[1]),
                "histogram": float(row.iloc[2]),
            })
    return result


def _supertrend_to_list(timestamps: pd.Series, supertrend: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert SuperTrend DataFrame to list"""
    result = []
    # SuperTrend returns usually 2 columns: SUPERT_length_mult (trend line), SUPERTd_length_mult (direction 1/-1)
    # We need to identify them dynamically or assume position
    if supertrend.empty:
        return []
        
    cols = supertrend.columns.tolist()
    # Usually first col is value, second is direction (or vice versa? pandas_ta varies)
    # pandas_ta: SUPERT_7_3.0, SUPERTd_7_3.0, SUPERTl_7_3.0, SUPERTs_7_3.0
    
    val_col = [c for c in cols if c.startswith("SUPERT_")][0]
    dir_col = [c for c in cols if c.startswith("SUPERTd_")][0]
    
    for i, ts in enumerate(timestamps):
        val = supertrend[val_col].iloc[i]
        direction = supertrend[dir_col].iloc[i]
        
        if pd.notna(val):
            result.append({
                "timestamp": int(ts),
                "value": float(val),
                "trend": "bullish" if direction > 0 else "bearish"
            })
    return result

def _fib_to_list(timestamps: pd.Series, high: pd.Series, low: pd.Series, lookback: int) -> List[Dict[str, Any]]:
    """Calculate Auto Fib levels based on recent high/low"""
    # This is a simplification. Real Auto Fib might need pivot detection.
    # We'll stick to a simple lookback high/low for now.
    
    # We only return the levels for the *last* candle to draw lines, 
    # or we can return a series. For "Overlay", we usually want a series.
    result = []
    
    # Rolling max/min
    roll_high = high.rolling(lookback).max()
    roll_low = low.rolling(lookback).min()
    
    for i, ts in enumerate(timestamps):
        h = roll_high.iloc[i]
        l = roll_low.iloc[i]
        
        if pd.notna(h) and pd.notna(l) and h != l:
            diff = h - l
            result.append({
                "timestamp": int(ts),
                "top": float(h),
                "fib_0_236": float(h - (diff * 0.236)),
                "fib_0_382": float(h - (diff * 0.382)),
                "fib_0_5": float(h - (diff * 0.5)),
                "fib_0_618": float(h - (diff * 0.618)),
                "fib_0_786": float(h - (diff * 0.786)),
                "bottom": float(l)
            })
            
    return result


def _fvg_to_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect 3-candle Fair Value Gaps (FVG)"""
    result = []
    # Need at least 3 candles to detect FVG
    if len(df) < 3:
        return []
        
    for i in range(2, len(df)):
        # Bullish FVG: Low of current (i) > High of (i-2)
        if df['low'].iloc[i] > df['high'].iloc[i-2]:
            ts = df['timestamp'].iloc[i]
            result.append({
                "timestamp": int(ts.timestamp() * 1000) if isinstance(ts, pd.Timestamp) else int(ts),
                "type": "bullish",
                "bottom": float(df['high'].iloc[i-2]),
                "top": float(df['low'].iloc[i])
            })
            
        # Bearish FVG: High of current (i) < Low of (i-2)
        elif df['high'].iloc[i] < df['low'].iloc[i-2]:
            ts = df['timestamp'].iloc[i]
            result.append({
                "timestamp": int(ts.timestamp() * 1000) if isinstance(ts, pd.Timestamp) else int(ts),
                "type": "bearish",
                "top": float(df['low'].iloc[i-2]),
                "bottom": float(df['high'].iloc[i])
            })
            
    return result


def _mss_to_list(df: pd.DataFrame, lookback: int = 2) -> List[Dict[str, Any]]:
    """Detect Market Structure Shifts (MSS)"""
    result = []
    if len(df) < (lookback * 2 + 1):
        return []

    last_pivot_high = None
    last_pivot_low = None
    
    # Note: loop stops `lookback` candles before the end — the inner comparison accesses i+j,
    # so the last `lookback` candles (default 2) can never qualify as pivots. MSS detection
    # is intentionally lagged by this amount.
    for i in range(lookback, len(df) - lookback):
        # 1. Detect Pivot High
        is_pivot_high = True
        for j in range(1, lookback + 1):
            if df['high'].iloc[i] <= df['high'].iloc[i-j] or df['high'].iloc[i] <= df['high'].iloc[i+j]:
                is_pivot_high = False
                break
        if is_pivot_high:
            last_pivot_high = df['high'].iloc[i]
            logger.debug(f"Pivot High found at {i}: {last_pivot_high}")

        # 2. Detect Pivot Low
        is_pivot_low = True
        for j in range(1, lookback + 1):
            if df['low'].iloc[i] >= df['low'].iloc[i-j] or df['low'].iloc[i] >= df['low'].iloc[i+j]:
                is_pivot_low = False
                break
        if is_pivot_low:
            last_pivot_low = df['low'].iloc[i]
            logger.debug(f"Pivot Low found at {i}: {last_pivot_low}")

        # 3. Detect Structural Breaks (MSS) - Checked every candle
        # Bullish MSS: Close > Last Pivot High
        if last_pivot_high and df['close'].iloc[i] > last_pivot_high:
            logger.info(f"Bullish MSS detected at {i}: {df['close'].iloc[i]} > {last_pivot_high}")
            ts = df['timestamp'].iloc[i]
            result.append({
                "timestamp": int(ts.timestamp() * 1000) if isinstance(ts, pd.Timestamp) else int(ts),
                "type": "bullish",
                "price": float(last_pivot_high)
            })
            last_pivot_high = None # Reset until next pivot

        # Bearish MSS: Close < Last Pivot Low
        elif last_pivot_low and df['close'].iloc[i] < last_pivot_low:
            logger.info(f"Bearish MSS detected at {i}: {df['close'].iloc[i]} < {last_pivot_low}")
            ts = df['timestamp'].iloc[i]
            result.append({
                "timestamp": int(ts.timestamp() * 1000) if isinstance(ts, pd.Timestamp) else int(ts),
                "type": "bearish",
                "price": float(last_pivot_low)
            })
            last_pivot_low = None
            
    return result


def _sweep_to_list(df: pd.DataFrame, lookback: int = 24) -> List[Dict[str, Any]]:
    """Detect Liquidity Sweeps (ICT/SMC)"""
    result = []
    if len(df) < lookback + 1:
        return []

    # Calculate rolling max/min of previous candles
    # shift(1) to exclude the current candle
    prev_highs = df['high'].shift(1).rolling(lookback).max()
    prev_lows = df['low'].shift(1).rolling(lookback).min()

    for i in range(lookback, len(df)):
        h_level = prev_highs.iloc[i]
        l_level = prev_lows.iloc[i]
        
        if pd.isna(h_level) or pd.isna(l_level):
            continue

        # Bearish Sweep: High > prev_high AND Close < prev_high
        if df['high'].iloc[i] > h_level and df['close'].iloc[i] < h_level:
            ts = df['timestamp'].iloc[i]
            result.append({
                "timestamp": int(ts.timestamp() * 1000) if isinstance(ts, pd.Timestamp) else int(ts),
                "type": "bearish",
                "level": float(h_level)
            })
            logger.info(f"Bearish Sweep detected at {i}: High swept {h_level}")

        # Bullish Sweep: Low < prev_low AND Close > prev_low
        elif df['low'].iloc[i] < l_level and df['close'].iloc[i] > l_level:
            ts = df['timestamp'].iloc[i]
            result.append({
                "timestamp": int(ts.timestamp() * 1000) if isinstance(ts, pd.Timestamp) else int(ts),
                "type": "bullish",
                "level": float(l_level)
            })
            logger.info(f"Bullish Sweep detected at {i}: Low swept {l_level}")

    return result

