from pydantic import BaseModel

from app.providers import Candle as ProviderCandle


class MarketTicker(BaseModel):
    symbol: str
    price: float
    change_24h: float | None = None
    volume_24h: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    market_cap: float | None = None
    rank: int | None = None
    name: str | None = None
    provider: str = "okx"


class MarketSummary(BaseModel):
    gainers: list[MarketTicker] = []
    losers: list[MarketTicker] = []
    top_volume: list[MarketTicker] = []
    timestamp: int  # Epoch ms


class OHLCVResponse(BaseModel):
    """Response model for OHLCV endpoint"""

    symbol: str
    timeframe: str
    provider: str
    candles: list[ProviderCandle]


class TickerResponse(BaseModel):
    """Response model for ticker price"""

    symbol: str
    price: float | None
    provider: str


class CoinInfo(BaseModel):
    """Coin information for display"""

    rank: int
    symbol: str
    name: str
    price: float
    change_1h: float | None = None
    change_24h: float | None = None
    change_7d: float | None = None
    volume_24h: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None
    market_cap: float | None = None
    image: str | None = None
    sparkline_in_7d: list[float] | None = None


class CoinsResponse(BaseModel):
    """Paginated coins list response"""

    coins: list[CoinInfo]
    total: int
    page: int
    page_size: int


class MarketSummaryResponse(BaseModel):
    """Market summary statistics"""

    total_coins: int
    provider: str
    top_gainers: list[CoinInfo] = []
    top_losers: list[CoinInfo] = []
    top_volume: list[CoinInfo] = []
