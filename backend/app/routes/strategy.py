"""
Strategy API Routes
Endpoints for running technical strategies on market data
"""

import asyncio
import logging
import time
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import pandas as pd
from sqlmodel import select
from app.constants import TIMEFRAME_MS, DEFAULT_TIMEFRAME_MS, active_provider_name

logger = logging.getLogger(__name__)

from app.strategies.oracle import OracleStrategy
from app.strategies.titan import TitanStrategy
from app.storage import Database, RedisClient
from app.schemas.candle import Candle as DbCandle
from app.providers import get_provider, DataProvider, BinanceProvider, OKXProvider

router = APIRouter(prefix="/api/strategy", tags=["strategy"])

# Singleton strategy instance
oracle = OracleStrategy()
titan = TitanStrategy()

async def get_candles_df(symbol: str, timeframe: str, limit: int = 500, provider: Optional[DataProvider] = None) -> pd.DataFrame:
    """
    Helper to get candles as DataFrame.
    Fetches from DB first, then falls back to Binance if insufficient.
    """
    # 1. Try DB (filter by active provider to avoid duplicate timestamps)
    active_provider = active_provider_name() if provider is None else provider.name
    async with Database.get_session() as session:
        statement = select(DbCandle).where(
            DbCandle.symbol == symbol,
            DbCandle.timeframe == timeframe,
            DbCandle.provider == active_provider,
        ).order_by(DbCandle.timestamp.desc()).limit(limit)
        
        results = await session.execute(statement)
        db_candles = results.scalars().all()
    
    # 2. Check sufficiency
    # We need enough candles AND they must be fresh
    now_ms = int(time.time() * 1000)
    
    # Calculate timeframe in ms
    tf_ms = TIMEFRAME_MS.get(timeframe, DEFAULT_TIMEFRAME_MS)

    is_count_sufficient = len(db_candles) >= (limit * 0.8)

    is_fresh = False
    if db_candles:
        last_candle_ts = db_candles[0].timestamp  # Sorted desc, so 0 is latest
        # Stale if the latest candle is older than 1 full timeframe period
        is_fresh = (now_ms - last_candle_ts) < tf_ms
        
    is_sufficient = is_count_sufficient and is_fresh
    
    # 3. Fetch from exchange if missing/stale
    if not is_sufficient:
        try:
            local_provider = provider or get_provider()
            try:
                fetch_limit = min(limit, 1000)
                
                logger.info(f"Fetching {timeframe} for {symbol} from {local_provider.name}")
                fresh = await local_provider.get_ohlcv(symbol, timeframe=timeframe, limit=fetch_limit)
                
                # Save to DB (Async)
                async with Database.get_session() as session:
                    for c in fresh:
                        candle_db = DbCandle(
                            symbol=symbol,
                            provider=local_provider.name,
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
             logger.error(f"Failed to fetch strategy data for {symbol} {timeframe}: {e}")
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
    micro_tf: str = Query(default="4h", description="Timeframe for voters"),
    macro_tf: str = Query(default="1d", description="Timeframe for trend")
):
    """
    Runs the Oracle Strategy on a symbol.
    Uses Prophet logic (Trend Following with Macro Context).
    """
    try:
        cache_key = f"strategy:oracle:{symbol}:{micro_tf}:{macro_tf}"
        cached = await RedisClient.get_json(cache_key)
        if cached:
            return cached

        # Fetch data concurrently
        df_micro, df_macro = await asyncio.gather(
            get_candles_df(symbol, micro_tf, limit=500),
            get_candles_df(symbol, macro_tf, limit=200),
        )

        if df_micro.empty or df_macro.empty:
             raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")

        # Run Strategy
        result = oracle.analyze(df_micro, df_macro)

        # Add metadata
        result['symbol'] = symbol
        result['micro_tf'] = micro_tf
        result['macro_tf'] = macro_tf
        result['price'] = df_micro.iloc[-1]['close']
        result['last_updated'] = int(time.time() * 1000)

        await RedisClient.set_json(cache_key, result, ttl=60)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Oracle strategy error for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/titan/{symbol:path}")
async def get_titan_strategy(
    symbol: str,
    timeframe: str = Query(default="4h", description="Timeframe for analysis"),
    provider: Optional[str] = Query(default=None, description="Data provider override: 'binance' or 'okx'"),
):
    """
    Runs the Titan Unified Trading System on a symbol.
    """
    try:
        provider_name = provider.lower() if provider else None
        if provider_name and provider_name not in ("binance", "okx"):
            raise HTTPException(status_code=400, detail="provider must be 'binance' or 'okx'")

        cache_key = f"strategy:titan:{symbol}:{timeframe}:{provider_name or 'default'}"
        cached = await RedisClient.get_json(cache_key)
        if cached:
            return cached

        # Instantiate a one-off provider if an override was requested
        override_provider: Optional[DataProvider] = None
        if provider_name == "okx":
            override_provider = OKXProvider()
        elif provider_name == "binance":
            override_provider = BinanceProvider()

        try:
            # Fetch sufficient data for 200 EMA + lookback
            df = await get_candles_df(symbol, timeframe, limit=300, provider=override_provider)
        finally:
            if override_provider is not None:
                await override_provider.close()

        if df.empty:
             raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")

        # Run Strategy (pass symbol for per-symbol risk overrides)
        result = titan.analyze(df, symbol=symbol)

        # Add metadata
        result['symbol'] = symbol
        result['timeframe'] = timeframe
        result['provider'] = provider_name or active_provider_name()
        result['price'] = df.iloc[-1]['close']
        result['last_updated'] = int(time.time() * 1000)

        await RedisClient.set_json(cache_key, result, ttl=60)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Titan strategy error for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/regime")
async def get_market_regime():
    """
    Returns the current market regime based on BTC weekly EMA50.
    
    BULL: BTC weekly close > EMA50 → HODL, long-only alts
    BEAR: BTC weekly close < EMA50 → shorts, stablecoins
    
    Also returns anticipation: distance to EMA50 and next cross target.
    """
    try:
        # Canonical regime key shared with signal_log + worker (single source of truth).
        from app.jobs.signal_log import (
            compute_btc_weekly_regime,
            REGIME_CACHE_KEY,
            REGIME_CACHE_TTL,
        )

        cached = await RedisClient.get_json(REGIME_CACHE_KEY)
        if cached and cached.get("regime") in ("BULL", "BEAR"):
            return cached

        result = await compute_btc_weekly_regime()
        await RedisClient.set_json(REGIME_CACHE_KEY, result, ttl=REGIME_CACHE_TTL)
        return result

    except Exception as e:
        logger.error(f"Regime analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
