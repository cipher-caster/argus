"""
Indicator API Routes
Endpoints for listing and calculating technical indicators
"""

import logging
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.constants import DEFAULT_TIMEFRAME_MS, TIMEFRAME_MS, active_provider_name
from app.exceptions import CacheError, CalculationError, DataProviderError, ValidationError
from app.indicators import (
    IndicatorDefinition,
    IndicatorResult,
    calculate_indicator,
    get_available_indicators,
)
from app.indicators.market_indicators import (
    calculate_adx,
    calculate_average_rsi,
    calculate_btc_dominance,
    calculate_market_cap_stats,
    calculate_volatility,
)
from app.routes.market import get_provider
from app.storage import RedisClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/indicators", tags=["indicators"])


class IndicatorRequest(BaseModel):
    """Request model for calculating indicators"""

    type: str
    params: dict[str, Any] = {}


class CalculateRequest(BaseModel):
    """Request to calculate multiple indicators"""

    symbol: str
    timeframe: str = "1h"
    limit: int = 300
    indicators: list[IndicatorRequest]
    # Exclusive upper bound (ms epoch) for the candle window. Set when the user
    # scrolls back in time so indicators match the visible chart range.
    end_timestamp: int | None = None


class CalculateResponse(BaseModel):
    """Response with calculated indicator data"""

    symbol: str
    timeframe: str
    results: list[IndicatorResult]


@router.get("/", response_model=list[IndicatorDefinition])
async def list_indicators():
    """Get list of all available indicators with their parameters"""
    return get_available_indicators()


@router.post("/calculate", response_model=CalculateResponse)
async def calculate_indicators(request: CalculateRequest):
    """
    Calculate one or more indicators for a symbol

    Example request:
    ```json
    {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "indicators": [
            {"type": "ema", "params": {"length": 50}},
            {"type": "ema", "params": {"length": 200}},
            {"type": "rsi", "params": {"length": 14}}
        ]
    }
    ```
    """
    try:
        # Fetch OHLCV data from Database (Historical)
        # We assume the data is already populated by the main OHLCV endpoint (Redis/Worker/Market Route)
        # This allows indicators to be calculated on the full available history in DB
        from sqlmodel import select

        from app.schemas.candle import Candle as DbCandle
        from app.storage import Database

        async with Database.get_session() as session:
            active_provider = active_provider_name()
            query = select(DbCandle).where(
                DbCandle.symbol == request.symbol,
                DbCandle.timeframe == request.timeframe,
                DbCandle.provider == active_provider,
            )
            if request.end_timestamp is not None:
                query = query.where(DbCandle.timestamp < request.end_timestamp)
            query = query.order_by(DbCandle.timestamp.desc()).limit(request.limit)

            results = await session.execute(query)
            db_candles = results.scalars().all()

        if not db_candles:
            # Fallback for empty DB (e.g. fresh install) - try provider once
            logger.warning(
                f"No data in DB for {request.symbol} {request.timeframe}. Fetching from provider..."
            )
            provider = get_provider()
            try:
                since = None
                if request.end_timestamp is not None:
                    tf_ms = TIMEFRAME_MS.get(request.timeframe, DEFAULT_TIMEFRAME_MS)
                    since = request.end_timestamp - (request.limit * tf_ms)
                candles = await provider.get_ohlcv(
                    request.symbol, request.timeframe, request.limit, since=since
                )
            except Exception as e:
                raise DataProviderError(f"Failed to fetch from provider: {e}")
            if request.end_timestamp is not None:
                # `since` only bounds the window from below; enforce the upper bound.
                candles = [c for c in candles if c.timestamp < request.end_timestamp]
        else:
            # Sort ascending for calculation (oldest to newest)
            db_candles = sorted(db_candles, key=lambda x: x.timestamp)
            candles = db_candles

        # Convert to DataFrame
        df = pd.DataFrame(
            [
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in candles
            ]
        )

        if df.empty:
            raise ValidationError(
                f"No candle data available for {request.symbol} {request.timeframe}"
            )

        # Calculate each indicator
        results = []
        for ind_request in request.indicators:
            try:
                result = calculate_indicator(df, ind_request.type, ind_request.params)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to calculate {ind_request.type}: {e}")
                continue

        logger.info(
            f"Calculated {len(results)}/{len(request.indicators)} indicators for {request.symbol}"
        )

        return CalculateResponse(
            symbol=request.symbol, timeframe=request.timeframe, results=results
        )

    except DataProviderError as e:
        logger.error(f"Provider error calculating indicators: {e}")
        raise HTTPException(status_code=503, detail="Data provider error")
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to calculate indicators: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate indicators")


@router.get("/market/dashboard")
async def get_market_dashboard_indicators():
    """
    Get dashboard-level market indicators:
    - BTC Volatility (from BTC/USDT daily returns)
    - Market ADX (trend strength from BTC/USDT)
    - Total Market Cap (aggregated from all tickers)
    - BTC Dominance (BTC market cap / total)

    Returns:
        Dict with all 4 indicator values and sparkline data
    """
    from datetime import datetime

    from sqlmodel import select

    from app.schemas.candle import Candle as DbCandle
    from app.storage import Database

    DASHBOARD_CACHE_KEY = "indicators:market:dashboard"
    DASHBOARD_CACHE_TTL = 300  # 5 minutes

    cached = await RedisClient.get_json(DASHBOARD_CACHE_KEY)
    if cached:
        return cached

    result = {
        "btc_volatility": None,
        "market_adx": None,
        "total_market_cap": None,
        "btc_dominance": None,
        "updated_at": datetime.utcnow().isoformat(),
    }

    try:
        # Fetch BTC/USDT daily candles for volatility + ADX calculation
        async with Database.get_session() as session:
            active_provider = active_provider_name()
            query = (
                select(DbCandle)
                .where(
                    DbCandle.symbol == "BTC/USDT",
                    DbCandle.timeframe == "1d",
                    DbCandle.provider == active_provider,
                )
                .order_by(DbCandle.timestamp.desc())
                .limit(30)
            )

            db_result = await session.execute(query)
            db_candles = db_result.scalars().all()

        if db_candles:
            # Sort ascending (oldest to newest)
            db_candles = sorted(db_candles, key=lambda x: x.timestamp)

            closes = [c.close for c in db_candles]
            highs = [c.high for c in db_candles]
            lows = [c.low for c in db_candles]

            # Calculate BTC Volatility
            vol_indicator = calculate_volatility(closes, period=14)
            result["btc_volatility"] = vol_indicator.model_dump()

            # Calculate Market ADX
            adx_indicator = calculate_adx(highs, lows, closes, period=14)
            result["market_adx"] = adx_indicator.model_dump()
        else:
            logger.warning("No BTC/USDT daily data available for volatility/ADX calculation")

        # Fetch ticker data from Redis for market cap calculations
        # Try snapshot first (rich data with market caps), then tickers (live volume only)
        snapshot = await RedisClient.get_json("market:snapshot")
        tickers = snapshot if snapshot else await RedisClient.get_json("market:tickers")

        if tickers:
            # Sort by MC (if available) or Volume
            sorted_tickers = sorted(
                tickers, key=lambda x: x.get("market_cap") or x.get("volume_24h") or 0, reverse=True
            )
            top_100 = sorted_tickers[:100]

            # Calculate Total Market Cap (or Volume if fallback)
            market_cap_stats = calculate_market_cap_stats(top_100)
            result["total_market_cap"] = market_cap_stats

            # Calculate BTC Dominance
            dominance = calculate_btc_dominance(top_100)
            result["btc_dominance"] = dominance.model_dump()

            # Calculate Average Crypto RSI
            avg_rsi = calculate_average_rsi(top_100)
            result["average_rsi"] = avg_rsi.model_dump()
        else:
            logger.warning("No ticker data available for market cap calculations")

        logger.info("Dashboard indicators calculated successfully")
        await RedisClient.set_json(DASHBOARD_CACHE_KEY, result, ttl=DASHBOARD_CACHE_TTL)
        return result

    except CacheError as e:
        logger.error(f"Cache error fetching dashboard indicators: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Cache unavailable")
    except CalculationError as e:
        logger.error(f"Calculation error in dashboard indicators: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate dashboard indicators")
    except Exception as e:
        logger.error(f"Failed to calculate dashboard indicators: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate dashboard indicators")
