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

class MarketHealthResponse(BaseModel):
    summary: Dict[str, Any]
    volatility: Dict[str, Any]

class LiquiditySweepItem(BaseModel):
    symbol: str
    bull_sweep: bool
    bear_sweep: bool
    swept_level: Optional[float]
    type: Optional[str]

class LiquiditySweepResponse(BaseModel):
    data: List[LiquiditySweepItem]

class RelativeStrengthItem(BaseModel):
    symbol: str
    performance_relative_pct: float
    strength: str
    current_ratio: float

class RelativeStrengthResponse(BaseModel):
    data: List[RelativeStrengthItem]

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

class OracleSignalSummaryResponse(BaseModel):
    bullish_pct: float
    bearish_pct: float
    top_signals: List[str] # e.g. ["SOL STRONG_BUY", "ETH BUY"]
    market_state: str

# New Analytics Engines
class TrendRadarItem(BaseModel):
    symbol: str
    price: float
    ema200: float
    distance_pct: float
    status: str
    volume: float

class TrendRadarResponse(BaseModel):
    map: List[TrendRadarItem]
    buckets: Dict[str, List[str]]
    summary: Dict[str, int]

class StructureItem(BaseModel):
    symbol: str
    price: float
    monday_high: float
    monday_low: float
    status: str
    range_pct: float

class StructureResponse(BaseModel):
    data: List[StructureItem]

class ConfluenceMetrics(BaseModel):
    total_analyzed: int
    sleeping_pct: float
    bullish_pct: float
    bearish_pct: float

class ConfluenceResponse(BaseModel):
    verdict: str
    metrics: ConfluenceMetrics
    score_distribution: Dict[int, int]

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

class TitanRadarResponse(BaseModel):
    data: List[TitanRadarItem]
