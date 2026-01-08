"""
Futures analytics data schemas
"""
from pydantic import BaseModel
from typing import List


class FundingRatePoint(BaseModel):
    """Single funding rate data point"""
    symbol: str
    timestamp: int  # milliseconds
    funding_rate: float


class OpenInterestPoint(BaseModel):
    """Open interest at a point in time"""
    symbol: str
    timestamp: int  # milliseconds
    open_interest: float  # in contracts
    open_interest_value: float  # in USD


class LongShortRatioPoint(BaseModel):
    """Long/Short ratio at a point in time"""
    symbol: str
    timestamp: int  # milliseconds
    long_account: float
    short_account: float
    long_short_ratio: float


class FundingRateResponse(BaseModel):
    """Funding rate history response"""
    symbol: str
    data: List[FundingRatePoint]


class OpenInterestResponse(BaseModel):
    """Open interest history response"""
    symbol: str
    data: List[OpenInterestPoint]


class LongShortRatioResponse(BaseModel):
    """Long/Short ratio history response"""
    symbol: str
    data: List[LongShortRatioPoint]
