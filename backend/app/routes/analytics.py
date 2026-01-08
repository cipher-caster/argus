"""
Futures analytics API routes
Provides funding rate, open interest, and long/short ratio data from Binance
"""
import httpx
from fastapi import APIRouter, Query, HTTPException
from typing import List
from app.schemas.analytics import (
    FundingRatePoint,
    FundingRateResponse,
    OpenInterestPoint,
    OpenInterestResponse,
    LongShortRatioPoint,
    LongShortRatioResponse,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

BINANCE_FUTURES_BASE = "https://fapi.binance.com"


@router.get("/funding-rate", response_model=FundingRateResponse)
async def get_funding_rate(
    symbol: str = Query(default="BTCUSDT", description="Trading pair symbol"),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of data points"),
):
    """
    Get funding rate history for a symbol.
    Funding rate is charged every 8 hours.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BINANCE_FUTURES_BASE}/fapi/v1/fundingRate",
                params={"symbol": symbol, "limit": limit},
                timeout=10.0,
            )
            response.raise_for_status()
            raw_data = response.json()
            
            data = [
                FundingRatePoint(
                    symbol=item["symbol"],
                    timestamp=item["fundingTime"],
                    funding_rate=float(item["fundingRate"]),
                )
                for item in raw_data
            ]
            
            return FundingRateResponse(symbol=symbol, data=data)
            
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Binance API error: {str(e)}")


@router.get("/open-interest", response_model=OpenInterestResponse)
async def get_open_interest(
    symbol: str = Query(default="BTCUSDT", description="Trading pair symbol"),
    period: str = Query(default="1h", description="Period: 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d"),
    limit: int = Query(default=100, ge=1, le=500, description="Number of data points"),
):
    """
    Get open interest history for a symbol.
    Shows total open positions in the market.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BINANCE_FUTURES_BASE}/futures/data/openInterestHist",
                params={"symbol": symbol, "period": period, "limit": limit},
                timeout=10.0,
            )
            response.raise_for_status()
            raw_data = response.json()
            
            data = [
                OpenInterestPoint(
                    symbol=item["symbol"],
                    timestamp=item["timestamp"],
                    open_interest=float(item["sumOpenInterest"]),
                    open_interest_value=float(item["sumOpenInterestValue"]),
                )
                for item in raw_data
            ]
            
            return OpenInterestResponse(symbol=symbol, data=data)
            
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Binance API error: {str(e)}")


@router.get("/long-short-ratio", response_model=LongShortRatioResponse)
async def get_long_short_ratio(
    symbol: str = Query(default="BTCUSDT", description="Trading pair symbol"),
    period: str = Query(default="1h", description="Period: 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d"),
    limit: int = Query(default=100, ge=1, le=500, description="Number of data points"),
):
    """
    Get global long/short account ratio.
    Shows what percentage of accounts are long vs short.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BINANCE_FUTURES_BASE}/futures/data/globalLongShortAccountRatio",
                params={"symbol": symbol, "period": period, "limit": limit},
                timeout=10.0,
            )
            response.raise_for_status()
            raw_data = response.json()
            
            data = [
                LongShortRatioPoint(
                    symbol=item["symbol"],
                    timestamp=item["timestamp"],
                    long_account=float(item["longAccount"]),
                    short_account=float(item["shortAccount"]),
                    long_short_ratio=float(item["longShortRatio"]),
                )
                for item in raw_data
            ]
            
            return LongShortRatioResponse(symbol=symbol, data=data)
            
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Binance API error: {str(e)}")


@router.get("/symbols")
async def get_supported_symbols():
    """Get list of commonly used futures symbols"""
    return {
        "symbols": [
            "BTCUSDT",
            "ETHUSDT",
            "SOLUSDT",
            "BNBUSDT",
            "XRPUSDT",
            "DOGEUSDT",
            "ADAUSDT",
            "AVAXUSDT",
        ],
        "default": "BTCUSDT"
    }
