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

class BestSetupItem(BaseModel):
    symbol: str
    direction: str       # LONG or SHORT
    conviction: int      # 0-100 combined score
    entry: float
    tp: float
    sl: float
    reason: str
    oracle_score: int
    titan_signal: str
    # Oracle backtest stats (None when < 10 trades — insufficient sample)
    win_rate: Optional[float] = None   # % of winning trades; break-even at 33.3% for 2:1 RR
    total_trades: Optional[int] = None
    # Eliz+Mayne MTF confluence: Titan signal direction confirmed on each timeframe
    # Eliz lane: 4h (entry trigger) + 1d (swing structure)
    # Mayne lane: 12h (higher bias) + 1w (macro/weekly direction)
    timeframe_confirmation: Optional[Dict[str, bool]] = None

class BestSetupsResponse(BaseModel):
    data: List[BestSetupItem]
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
