"""
Indicator API Routes
Endpoints for listing and calculating technical indicators
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
import pandas as pd

from app.indicators import (
    get_available_indicators,
    calculate_indicator,
    IndicatorDefinition,
    IndicatorResult
)
from app.indicators.market_indicators import (
    calculate_volatility,
    calculate_adx,
    calculate_market_cap_stats,
    calculate_btc_dominance
)
from app.routes.market import get_provider
from app.storage import RedisClient


router = APIRouter(prefix="/api/indicators", tags=["indicators"])


class IndicatorRequest(BaseModel):
    """Request model for calculating indicators"""
    type: str
    params: Dict[str, Any] = {}


class CalculateRequest(BaseModel):
    """Request to calculate multiple indicators"""
    symbol: str
    timeframe: str = "1h"
    limit: int = 300
    indicators: List[IndicatorRequest]


class CalculateResponse(BaseModel):
    """Response with calculated indicator data"""
    symbol: str
    timeframe: str
    results: List[IndicatorResult]


@router.get("/", response_model=List[IndicatorDefinition])
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
        from app.storage import Database
        from app.schemas.candle import Candle as DbCandle
        from sqlmodel import select
        
        async with Database.get_session() as session:
            query = select(DbCandle).where(
                DbCandle.symbol == request.symbol,
                DbCandle.timeframe == request.timeframe
            ).order_by(DbCandle.timestamp.desc()).limit(request.limit)
            
            results = await session.execute(query)
            db_candles = results.scalars().all()
            
        if not db_candles:
            # Fallback for empty DB (e.g. fresh install) - try provider once
            print(f"W: No data in DB for {request.symbol} {request.timeframe}. Fetching from provider...")
            provider = get_provider()
            candles = await provider.get_ohlcv(request.symbol, request.timeframe, request.limit)
        else:
            # Sort ascending for calculation (oldest to newest)
            db_candles = sorted(db_candles, key=lambda x: x.timestamp)
            candles = db_candles

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "timestamp": c.timestamp,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume
            }
            for c in candles
        ])
        
        # Calculate each indicator
        results = []
        for ind_request in request.indicators:
            result = calculate_indicator(df, ind_request.type, ind_request.params)
            if result:
                results.append(result)
        
        return CalculateResponse(
            symbol=request.symbol,
            timeframe=request.timeframe,
            results=results
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to calculate: {str(e)}")


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
    from app.storage import Database
    from app.schemas.candle import Candle as DbCandle
    from sqlmodel import select
    from datetime import datetime
    
    result = {
        "btc_volatility": None,
        "market_adx": None,
        "total_market_cap": None,
        "btc_dominance": None,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    try:
        # Fetch BTC/USDT daily candles for volatility + ADX calculation
        async with Database.get_session() as session:
            query = select(DbCandle).where(
                DbCandle.symbol == "BTC/USDT",
                DbCandle.timeframe == "1d"
            ).order_by(DbCandle.timestamp.desc()).limit(30)
            
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
        
        # Fetch ticker data from Redis for market cap calculations
        tickers = await RedisClient.get_json("market:tickers")
        
        if tickers:
            # Filter to top 100 by volume for market summary
            sorted_tickers = sorted(tickers, key=lambda x: x.get('volume_24h') or 0, reverse=True)
            top_100 = sorted_tickers[:100]
            
            # Calculate Total Volume (top 100)
            market_cap_stats = calculate_market_cap_stats(top_100)
            result["total_market_cap"] = market_cap_stats
            
            # Calculate BTC Dominance (top 100)
            dominance = calculate_btc_dominance(top_100)
            result["btc_dominance"] = dominance.model_dump()
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to calculate dashboard indicators: {str(e)}")

