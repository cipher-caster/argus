from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger
from typing import Optional

class Candle(SQLModel, table=True):
    __tablename__ = "candles"
    
    symbol: str = Field(primary_key=True, index=True)
    provider: str = Field(primary_key=True, default="binance")
    timeframe: str = Field(primary_key=True)
    timestamp: int = Field(primary_key=True, sa_type=BigInteger)  # Epoch milliseconds
    
    open: float
    high: float
    low: float
    close: float
    volume: float

    class Config:
        unique_together = ("symbol", "provider", "timeframe", "timestamp")
