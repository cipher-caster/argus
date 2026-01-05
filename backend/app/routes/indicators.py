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
from app.routes.market import get_provider


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
