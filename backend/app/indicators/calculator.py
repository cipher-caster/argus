"""
Indicator Calculator Module
Provides a registry of technical indicators with configurable parameters
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import pandas as pd
import pandas_ta as ta


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
            
    except Exception as e:
        print(f"Error calculating {indicator_name}: {e}")
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
