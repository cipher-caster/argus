"""
Futures analytics API routes
Uses CCXT-based BinanceProvider for data fetching
Redis caching for performance optimization
"""
import logging
import pandas as pd
import asyncio
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional

from app.schemas.analytics import (
    ScreenerResponse,
    MarketHealthResponse,
    LiquiditySweepResponse,
    LiquiditySweepItem,
    RelativeStrengthResponse,
    RelativeStrengthItem,
    MeanReversionResponse,
    MeanReversionItem,
    OracleSignalSummaryResponse
)

from app.routes.strategy import get_candles_df
from app.indicators.screener import run_oracle_screener
from app.indicators.market_health import calculate_market_health
from app.indicators.liquidity import detect_liquidity_sweeps
from app.indicators.relative_strength import calculate_relative_strength
from app.indicators.mean_reversion import detect_mean_reversion
from app.providers.binance_provider import BinanceProvider
from app.services.market_data import MarketDataService
from app.storage import RedisClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

# Cache TTL in seconds
CACHE_TTL = 60


@router.get("/symbols")
async def get_supported_symbols(limit: int = 20):
    """Get list of commonly used futures symbols"""
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    return {
        "symbols": symbols,
        "default": "BTCUSDT"
    }


async def fetch_all_candles(symbols: List[str], timeframe: str = "1h", limit: int = 250):
    """Helper to fetch candles for multiple symbols concurrently, reusing provider"""
    provider = BinanceProvider()
    try:
        tasks = [get_candles_df(sym, timeframe, limit, provider=provider) for sym in symbols]
        dataframes = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            sym: df for sym, df in zip(symbols, dataframes) 
            if not isinstance(df, Exception) and df is not None and not df.empty
        }
    finally:
        await provider.close()


@router.get("/screener", response_model=ScreenerResponse)
async def get_oracle_screener(limit: int = 50, timeframe: str = "1h"):
    """Get Oracle analysis for top coins with specific timeframe"""
    cache_key = f"analytics:screener:{timeframe}:{limit}"
    
    # Try cache first
    cached = await RedisClient.get_json(cache_key)
    if cached:
        logger.debug(f"Cache HIT: {cache_key}")
        return ScreenerResponse(data=cached)
    
    # Cache miss - compute fresh data
    logger.debug(f"Cache MISS: {cache_key}")
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    btc_df = df_data.get("BTCUSDT", pd.DataFrame())
    
    data = run_oracle_screener(df_data, btc_df)
    
    # Cache the result
    await RedisClient.set_json(cache_key, data, ttl=CACHE_TTL)
    return ScreenerResponse(data=data)


@router.get("/market-health", response_model=MarketHealthResponse)
async def get_market_health(limit: int = 100, timeframe: str = "1h"):
    """Get aggregate market health metrics with specific timeframe"""
    cache_key = f"analytics:health:{timeframe}:{limit}"
    
    cached = await RedisClient.get_json(cache_key)
    if cached:
        return MarketHealthResponse(**cached)
    
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    health = calculate_market_health(df_data)
    
    await RedisClient.set_json(cache_key, health, ttl=CACHE_TTL)
    return MarketHealthResponse(**health)


@router.get("/liquidity-sweeps", response_model=LiquiditySweepResponse)
async def get_liquidity_sweeps_analytics(limit: int = 50, timeframe: str = "1h"):
    """Identify coins sweeping major levels with specific timeframe"""
    cache_key = f"analytics:liquidity:{timeframe}:{limit}"
    
    cached = await RedisClient.get_json(cache_key)
    if cached:
        return LiquiditySweepResponse(data=[LiquiditySweepItem(**item) for item in cached])
    
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    
    # Calculate bars per week based on timeframe
    bars_per_week = {"15m": 672, "1h": 168, "4h": 42, "12h": 14, "1d": 7, "3d": 3, "1w": 1}
    weekly_window = bars_per_week.get(timeframe, 168)
    
    results = []
    for sym, df in df_data.items():
        # Pre-process some levels for sweep detection if not present
        if 'pwh' not in df.columns and len(df) > weekly_window:
            # Approximate Weekly High/Low based on timeframe
            df['pwh'] = df['high'].shift(1).rolling(weekly_window).max()
            df['pwl'] = df['low'].shift(1).rolling(weekly_window).min()
            
        sweep = detect_liquidity_sweeps(df)
        if sweep['bull_sweep'] or sweep['bear_sweep']:
            results.append(LiquiditySweepItem(symbol=sym, **sweep))
    
    # Cache as dicts for JSON serialization
    await RedisClient.set_json(cache_key, [r.model_dump() for r in results], ttl=CACHE_TTL)
    return LiquiditySweepResponse(data=results)


@router.get("/relative-strength", response_model=RelativeStrengthResponse)
async def get_relative_strength_analytics(limit: int = 50, timeframe: str = "1h"):
    """Compare altcoin performance vs BTC with specific timeframe"""
    cache_key = f"analytics:strength:{timeframe}:{limit}"
    
    cached = await RedisClient.get_json(cache_key)
    if cached:
        return RelativeStrengthResponse(data=[RelativeStrengthItem(**item) for item in cached])
    
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    btc_df = df_data.get("BTCUSDT", pd.DataFrame())
    
    results = []
    for sym, df in df_data.items():
        if sym == "BTCUSDT": continue
        rs = calculate_relative_strength(df, btc_df)
        results.append(RelativeStrengthItem(symbol=sym, **rs))
    
    await RedisClient.set_json(cache_key, [r.model_dump() for r in results], ttl=CACHE_TTL)
    return RelativeStrengthResponse(data=results)


@router.get("/contrarian-radar", response_model=MeanReversionResponse)
async def get_contrarian_radar(limit: int = 50, timeframe: str = "1h"):
    """Identify overextended coins for potential reversal with specific timeframe"""
    cache_key = f"analytics:contrarian:{timeframe}:{limit}"
    
    cached = await RedisClient.get_json(cache_key)
    if cached:
        return MeanReversionResponse(data=[MeanReversionItem(**item) for item in cached])
    
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    
    results = []
    for sym, df in df_data.items():
        rev = detect_mean_reversion(df)
        if rev['is_extended']:
            results.append(MeanReversionItem(symbol=sym, **rev))
    
    await RedisClient.set_json(cache_key, [r.model_dump() for r in results], ttl=CACHE_TTL)
    return MeanReversionResponse(data=results)


@router.get("/signal-summary", response_model=OracleSignalSummaryResponse)
async def get_oracle_signal_summary():
    """High-level summary for the dashboard - fixed at top 20 for performance"""
    cache_key = "analytics:signal-summary"
    
    cached = await RedisClient.get_json(cache_key)
    if cached:
        return OracleSignalSummaryResponse(**cached)
    
    symbols = await MarketDataService.get_top_symbols(limit=20)
    df_data = await fetch_all_candles(symbols)
    btc_df = df_data.get("BTCUSDT", pd.DataFrame())
    
    screener_data = run_oracle_screener(df_data, btc_df)
    health = calculate_market_health(df_data)
    
    bullish = len([s for s in screener_data if s['score'] >= 3])
    bearish = len([s for s in screener_data if s['score'] <= -3])
    
    top_signals = [f"{s['symbol']} {s['score']}/4" for s in screener_data if abs(s['score']) >= 3][:5]
    
    result = {
        "bullish_pct": round((bullish / len(screener_data)) * 100, 1) if screener_data else 0,
        "bearish_pct": round((bearish / len(screener_data)) * 100, 1) if screener_data else 0,
        "top_signals": top_signals,
        "market_state": (
            "STRONG BULL" if health['summary']['bullish_pct'] > 60 
            else "STRONG BEAR" if health['summary']['bearish_pct'] > 60 
            else "NEUTRAL"
        )
    }
    
    await RedisClient.set_json(cache_key, result, ttl=CACHE_TTL)
    return OracleSignalSummaryResponse(**result)

