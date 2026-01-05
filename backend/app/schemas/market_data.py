from pydantic import BaseModel
from typing import Optional, List

class MarketTicker(BaseModel):
    symbol: str
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    rank: Optional[int] = None
    name: Optional[str] = None
    provider: str = "binance"
    
class MarketSummary(BaseModel):
    gainers: List[MarketTicker] = []
    losers: List[MarketTicker] = []
    top_volume: List[MarketTicker] = []
    timestamp: int # Epoch ms
