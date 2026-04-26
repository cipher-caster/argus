"""
Futures analytics data schemas
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.jobs.signal_log import DEFAULT_WATCHLIST, DEFAULT_MIN_TITAN_CONFIDENCE, DEFAULT_REVIEW_DAYS


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
    mss_type: Optional[str] = None
    sweep_type: Optional[str] = None

class TitanRadarResponse(BaseModel):
    data: List[TitanRadarItem]
    last_updated: int = 0

class SignalLogConfig(BaseModel):
    watchlist: List[str] = DEFAULT_WATCHLIST
    min_titan_confidence: int = DEFAULT_MIN_TITAN_CONFIDENCE
    review_days: int = DEFAULT_REVIEW_DAYS
    block_sleeping: bool = True
    block_volatile: bool = True
    macro_guard: bool = True


class SignalLogItem(BaseModel):
    id: int
    symbol: str
    direction: str          # LONG | SHORT
    timeframe: str
    entry: float
    tp: float
    sl: float
    conviction: int
    oracle_signal: str
    titan_signal: str
    oracle_score: int
    titan_confidence: int
    market_state: str
    fired_reason: str
    fired_at: int           # epoch ms
    source: str = "live"   # "live" | "backtest" | "scanner"
    provider: str = "okx"  # "binance" | "okx"
    outcome: str            # OPEN | WIN | LOSS | REVIEW | REJECTED
    resolved_at: Optional[int] = None
    resolved_price: Optional[float] = None
    # Resolution-time context (v0.9.1)
    regime_at_resolution: Optional[str] = None
    btc_price_at_resolution: Optional[float] = None
    time_to_resolution_ms: Optional[int] = None
    rejection_reason: Optional[str] = None
    # Entry-time context (Phase 18)
    regime_at_signal: Optional[str] = None
    btc_price_at_signal: Optional[float] = None
    methodology_version: Optional[str] = None

class SignalLogSummary(BaseModel):
    total: int
    open: int
    win: int
    loss: int
    review: int
    rejected: Optional[int] = None
    win_rate: Optional[float] = None   # WIN / (WIN + LOSS), None if no closed trades

class SignalLogResponse(BaseModel):
    data: List[SignalLogItem]
    summary: SignalLogSummary
    total: int = 0  # Total count of matching signals (for pagination)
    last_updated: int = 0
