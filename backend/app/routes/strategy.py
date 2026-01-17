"""
Strategy API Routes
Endpoints for running technical strategies on market data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import pandas as pd
from sqlmodel import select

from app.strategies.oracle import OracleStrategy
from app.storage import Database
from app.schemas.candle import Candle as DbCandle
from app.providers.binance_provider import BinanceProvider

router = APIRouter(prefix="/api/strategy", tags=["strategy"])

# Singleton strategy instance
oracle = OracleStrategy()

async def get_candles_df(symbol: str, timeframe: str, limit: int = 500, provider: Optional[BinanceProvider] = None) -> pd.DataFrame:
    """
    Helper to get candles as DataFrame.
    Fetches from DB first, then falls back to Binance if insufficient.
    """
    # 1. Try DB
    async with Database.get_session() as session:
        statement = select(DbCandle).where(
            DbCandle.symbol == symbol,
            DbCandle.timeframe == timeframe
        ).order_by(DbCandle.timestamp.desc()).limit(limit)
        
        results = await session.execute(statement)
        db_candles = results.scalars().all()
    
    # 2. Check sufficiency
    is_sufficient = len(db_candles) >= (limit * 0.8) # Allow some tolerance
    
    # 3. Fetch from Binance if missing/stale
    if not is_sufficient:
        try:
            local_provider = provider or BinanceProvider()
            try:
                # Calculate since timestamp
                timeframe_ms = {
                    '1h': 60 * 60 * 1000,
                    '1d': 24 * 60 * 60 * 1000,
                }.get(timeframe, 60 * 60 * 1000)
                
                # Fetch 2x limit to be safe
                fetch_limit = limit if limit <= 1000 else 1000
                
                print(f"I: Fetching {timeframe} for {symbol} strategy...")
                fresh = await local_provider.get_ohlcv(symbol, timeframe=timeframe, limit=fetch_limit)
                
                # Save to DB (Async)
                async with Database.get_session() as session:
                    for c in fresh:
                        candle_db = DbCandle(
                            symbol=symbol,
                            provider="binance",
                            timeframe=timeframe,
                            timestamp=c.timestamp,
                            open=c.open,
                            high=c.high,
                            low=c.low,
                            close=c.close,
                            volume=c.volume
                        )
                        await session.merge(candle_db)
                    await session.commit()
                
                # Use fresh data directly
                data = [{
                    'timestamp': c.timestamp,
                    'open': c.open,
                    'high': c.high,
                    'low': c.low,
                    'close': c.close,
                    'volume': c.volume
                } for c in fresh]
                
            finally:
                if not provider:  # Only close if we created it locally
                    await local_provider.close()
        except Exception as e:
             print(f"E: Failed to fetch strategy data: {e}")
             return pd.DataFrame()
    else:
        # Use DB data
        data = [{
            'timestamp': c.timestamp,
            'open': c.open,
            'high': c.high,
            'low': c.low,
            'close': c.close,
            'volume': c.volume
        } for c in db_candles]
        
    # 4. Create DataFrame
    if not data:
        return pd.DataFrame()
        
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df


@router.get("/oracle/{symbol:path}")
async def get_oracle_strategy(
    symbol: str,
    micro_tf: str = Query(default="1h", description="Timeframe for voters"),
    macro_tf: str = Query(default="1d", description="Timeframe for trend"),
    strategy_mode: str = Query(default="prophet", pattern="^(prophet|earnest)$")
):
    """
    Runs the Oracle Strategy on a symbol.
    Modes:
    - prophet: Trend Following (Requires Daily Alignment)
    - earnest: Pure Momentum (Scalping/Counter-trend)
    """
    try:
        # Fetch Data concurrently could be better, but sequential is safer for now
        df_micro = await get_candles_df(symbol, micro_tf, limit=500)
        df_macro = await get_candles_df(symbol, macro_tf, limit=200)
        
        if df_micro.empty or df_macro.empty:
             raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")
             
        # Run Strategy
        result = oracle.analyze(df_micro, df_macro, mode=strategy_mode)
        
        # Add metadata
        result['symbol'] = symbol
        result['micro_tf'] = micro_tf
        result['macro_tf'] = macro_tf
        result['price'] = df_micro.iloc[-1]['close']
        
        return result
        
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
