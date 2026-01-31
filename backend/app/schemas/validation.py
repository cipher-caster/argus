"""
Shared validation schemas for API requests.

Provides Pydantic models and validators for common request parameters
like symbols, timeframes, and limits to ensure data integrity across all endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SymbolValidator(BaseModel):
    """Validates cryptocurrency trading pair symbols."""
    
    symbol: str = Field(..., pattern=r'^[A-Z0-9]+/USDT$', description="Trading pair (e.g., BTC/USDT)")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol_format(cls, v: str) -> str:
        """Ensure symbol follows the SYMBOL/USDT format."""
        if not v.endswith('/USDT'):
            raise ValueError('Symbol must end with /USDT')
        base = v.split('/')[0]
        if not base.isalnum() or not base.isupper():
            raise ValueError('Base symbol must be uppercase alphanumeric')
        return v


class TimeframeValidator(BaseModel):
    """Validates timeframe parameters."""
    
    ALLOWED_TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w', '1M']
    
    timeframe: str = Field(default="1h", description="Candle timeframe")
    
    @field_validator('timeframe')
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        """Ensure timeframe is one of the allowed values."""
        if v not in cls.ALLOWED_TIMEFRAMES:
            raise ValueError(f'Timeframe must be one of {cls.ALLOWED_TIMEFRAMES}')
        return v


class LimitValidator(BaseModel):
    """Validates limit/count parameters."""
    
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of items to return")


class OHLCVRequest(SymbolValidator, TimeframeValidator, LimitValidator):
    """Request model for OHLCV data endpoints."""
    
    limit: int = Field(default=100, ge=1, le=1000)


class TickerRequest(SymbolValidator):
    """Request model for ticker data endpoints."""
    pass


class AnalyticsRequest(TimeframeValidator, LimitValidator):
    """Base request model for analytics endpoints."""
    
    limit: int = Field(default=50, ge=1, le=200, description="Number of symbols to analyze")


class ScreenerRequest(AnalyticsRequest):
    """Request model for screener endpoints."""
    pass


class MarketHealthRequest(AnalyticsRequest):
    """Request model for market health endpoints."""
    
    limit: int = Field(default=100, ge=1, le=200)


class IndicatorCalculationRequest(SymbolValidator, TimeframeValidator, LimitValidator):
    """Request model for indicator calculation endpoints."""
    
    limit: int = Field(default=300, ge=1, le=1000, description="Number of candles to fetch")
