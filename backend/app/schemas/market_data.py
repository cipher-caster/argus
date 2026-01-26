from pydantic import BaseModel
from typing import Optional, List
from app.providers import Candle as ProviderCandle

class MarketTicker(BaseModel):
    symbol: str
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    market_cap: Optional[float] = None
    rank: Optional[int] = None
    name: Optional[str] = None
    provider: str = "binance"
    
class MarketSummary(BaseModel):
    gainers: List[MarketTicker] = []
    losers: List[MarketTicker] = []
    top_volume: List[MarketTicker] = []
    timestamp: int # Epoch ms

class OHLCVResponse(BaseModel):
    """Response model for OHLCV endpoint"""
    symbol: str
    timeframe: str
    provider: str
    candles: List[ProviderCandle]

class TickerResponse(BaseModel):
    """Response model for ticker price"""
    symbol: str
    price: Optional[float]
    provider: str

class CoinInfo(BaseModel):
    """Coin information for display"""
    rank: int
    symbol: str
    name: str
    price: float
    change_1h: Optional[float] = None
    change_24h: Optional[float] = None
    change_7d: Optional[float] = None
    volume_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    market_cap: Optional[float] = None
    image: Optional[str] = None
    sparkline_in_7d: Optional[List[float]] = None

class CoinsResponse(BaseModel):
    """Paginated coins list response"""
    coins: List[CoinInfo]
    total: int
    page: int
    page_size: int

class MarketSummaryResponse(BaseModel):
    """Market summary statistics"""
    total_coins: int
    provider: str
    top_gainers: List[CoinInfo] = []
    top_losers: List[CoinInfo] = []
    top_volume: List[CoinInfo] = []
