"""
Futures analytics API routes
Uses CCXT-based BinanceProvider for data fetching
"""
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

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


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
        dataframes = await asyncio.gather(*tasks)
        return {sym: df for sym, df in zip(symbols, dataframes) if not (df is None or df.empty)}
    finally:
        await provider.close()

@router.get("/screener", response_model=ScreenerResponse)
async def get_oracle_screener(limit: int = 50, timeframe: str = "1h"):
    """Get Oracle analysis for top coins with specific timeframe"""
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    btc_df = df_data.get("BTCUSDT", pd.DataFrame())
    
    data = run_oracle_screener(df_data, btc_df)
    return ScreenerResponse(data=data)

@router.get("/market-health", response_model=MarketHealthResponse)
async def get_market_health(limit: int = 100, timeframe: str = "1h"):
    """Get aggregate market health metrics with specific timeframe"""
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    health = calculate_market_health(df_data)
    return MarketHealthResponse(**health)

@router.get("/liquidity-sweeps", response_model=LiquiditySweepResponse)
async def get_liquidity_sweeps_analytics(limit: int = 50, timeframe: str = "1h"):
    """Identify coins sweeping major levels with specific timeframe"""
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    
    results = []
    for sym, df in df_data.items():
        # Pre-process some levels for sweep detection if not present
        if 'pwh' not in df.columns and len(df) > 24:
            # Simple approximation of Weekly High from hourly data
            df['pwh'] = df['high'].shift(1).rolling(168).max()
            df['pwl'] = df['low'].shift(1).rolling(168).min()
            
        sweep = detect_liquidity_sweeps(df)
        if sweep['bull_sweep'] or sweep['bear_sweep']:
            results.append(LiquiditySweepItem(symbol=sym, **sweep))
            
    return LiquiditySweepResponse(data=results)

@router.get("/relative-strength", response_model=RelativeStrengthResponse)
async def get_relative_strength_analytics(limit: int = 50, timeframe: str = "1h"):
    """Compare altcoin performance vs BTC with specific timeframe"""
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    btc_df = df_data.get("BTCUSDT", pd.DataFrame())
    
    results = []
    for sym, df in df_data.items():
        if sym == "BTCUSDT": continue
        rs = calculate_relative_strength(df, btc_df)
        results.append(RelativeStrengthItem(symbol=sym, **rs))
        
    return RelativeStrengthResponse(data=results)

@router.get("/contrarian-radar", response_model=MeanReversionResponse)
async def get_contrarian_radar(limit: int = 50, timeframe: str = "1h"):
    """Identify overextended coins for potential reversal with specific timeframe"""
    symbols = await MarketDataService.get_top_symbols(limit=limit)
    df_data = await fetch_all_candles(symbols, timeframe=timeframe)
    
    results = []
    for sym, df in df_data.items():
        rev = detect_mean_reversion(df)
        if rev['is_extended']:
            results.append(MeanReversionItem(symbol=sym, **rev))
            
    return MeanReversionResponse(data=results)

@router.get("/signal-summary", response_model=OracleSignalSummaryResponse)
async def get_oracle_signal_summary():
    """High-level summary for the dashboard - fixed at top 20 for performance"""
    symbols = await MarketDataService.get_top_symbols(limit=20)
    df_data = await fetch_all_candles(symbols)
    btc_df = df_data.get("BTCUSDT", pd.DataFrame())
    
    screener_data = run_oracle_screener(df_data, btc_df)
    health = calculate_market_health(df_data)
    
    bullish = len([s for s in screener_data if s['score'] >= 3])
    bearish = len([s for s in screener_data if s['score'] <= -3])
    
    top_signals = [f"{s['symbol']} {s['score']}/4" for s in screener_data if abs(s['score']) >= 3][:5]
    
    return OracleSignalSummaryResponse(
        bullish_pct=round((bullish / len(screener_data)) * 100, 1) if screener_data else 0,
        bearish_pct=round((bearish / len(screener_data)) * 100, 1) if screener_data else 0,
        top_signals=top_signals,
        market_state=health['summary']['bullish_pct'] > 60 and "STRONG BULL" or (health['summary']['bearish_pct'] > 60 and "STRONG BEAR" or "NEUTRAL")
    )
