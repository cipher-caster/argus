"""
Liquidation data schemas for heatmap feature
"""
from pydantic import BaseModel
from typing import Dict, List, Optional


class LiquidationEvent(BaseModel):
    """Single liquidation event from Binance"""
    symbol: str
    side: str  # BUY = short liquidated, SELL = long liquidated
    price: float
    quantity: float
    timestamp: int  # milliseconds


class PriceBucket(BaseModel):
    """Aggregated liquidation volume at a price level"""
    price_level: float
    volume: float
    count: int = 1


class TimeBucket(BaseModel):
    """All liquidations within a time window"""
    timestamp: int  # bucket start time (seconds)
    price_buckets: Dict[str, float]  # price_level -> total_volume


class HeatmapCell(BaseModel):
    """Single cell in the heatmap grid"""
    time: int
    price: float
    intensity: float  # normalized 0-1


class OHLCVPoint(BaseModel):
    """Single candlestick for overlay"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float


class LiquidationHeatmapResponse(BaseModel):
    """Full heatmap response"""
    symbol: str
    time_buckets: List[TimeBucket]
    price_min: float
    price_max: float
    max_intensity: float
    ohlcv: List[OHLCVPoint]  # For candlestick overlay
    bucket_size_seconds: int
