"""
Futures analytics data schemas
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# New Analytics Schemas

class ScreenerItem(BaseModel):
    symbol: str
    price: float
    score: int
    confidence: str
    bias: str
    state: str
    liquidity: str
    strength_vs_btc: str
    opportunity: str
    advice: str

class ScreenerResponse(BaseModel):
    data: List[ScreenerItem]
    last_updated: int = 0

class RelativeStrengthItem(BaseModel):
    symbol: str
    performance_relative_pct: float
    strength: str
    current_ratio: float

class RelativeStrengthResponse(BaseModel):
    data: List[RelativeStrengthItem]
    last_updated: int = 0

class MeanReversionItem(BaseModel):
    symbol: str
    is_extended: bool
    extension_atr: float
    opportunity: str
    price: float
    mean: float
    target: float

class MeanReversionResponse(BaseModel):
    data: List[MeanReversionItem]
    last_updated: int = 0

class OracleSignalSummaryResponse(BaseModel):
    bullish_pct: float
    bearish_pct: float
    top_signals: List[str] # e.g. ["SOL STRONG_BUY", "ETH BUY"]
    market_state: str
    last_updated: int = 0

class TitanRadarItem(BaseModel):
    symbol: str
    price: float
    signal: str
    confidence: int
    trend: str
    momentum: str
    volatility: str
    entry: float
    tp: float
    sl: float
    advice: str
    reasons: List[str] = []

class TitanRadarResponse(BaseModel):
    data: List[TitanRadarItem]
    last_updated: int = 0
