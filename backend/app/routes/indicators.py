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
    provider = get_provider()
    
    try:
        # Fetch OHLCV data
        candles = await provider.get_ohlcv(
            request.symbol, 
            request.timeframe, 
            request.limit
        )
        
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
        raise HTTPException(status_code=400, detail=f"Failed to calculate: {str(e)}")
