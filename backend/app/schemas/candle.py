from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Index
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

    __table_args__ = (
        Index("ix_candles_symbol_tf_ts", "symbol", "timeframe", "timestamp"),
    )

    class Config:
        unique_together = ("symbol", "provider", "timeframe", "timestamp")
