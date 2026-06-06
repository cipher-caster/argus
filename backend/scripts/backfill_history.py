#!/usr/bin/env python3
"""
Historical Data Backfill Script
Fetches and stores historical OHLCV data for popular trading pairs.

Usage:
    docker compose exec backend python scripts/backfill_history.py
    docker compose exec backend python scripts/backfill_history.py --provider=okx
    docker compose exec backend python scripts/backfill_history.py --symbols=BTC/USDT,ETH/USDT
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.storage import Database
from app.providers import get_provider, BinanceProvider, OKXProvider
from app.schemas.candle import Candle

# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------

def _get_flag(prefix, default=None):
    for arg in sys.argv:
        if arg.startswith(prefix):
            return arg.split("=", 1)[1]
    return default


PROVIDER_NAME = (_get_flag("--provider=") or os.getenv("DATA_PROVIDER", "binance")).lower()
CUSTOM_SYMBOLS = _get_flag("--symbols=")
if CUSTOM_SYMBOLS:
    SYMBOLS = [s.strip() for s in CUSTOM_SYMBOLS.split(",") if s.strip()]
else:
    SYMBOLS = [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "BNB/USDT",
        "ZEC/USDT",
    ]

TIMEFRAMES = [
    "15m",
    "1h",
    "4h",
    "12h",
    "1d",
    "1w",
]

LIMIT = 1000  # Max candles per request

async def backfill_candles(provider, symbol: str, timeframe: str):
    """Fetch and store candles for a single symbol/timeframe combination."""
    print(f"  Fetching {symbol} {timeframe}...", end=" ", flush=True)
    
    try:
        candles_data = await provider.get_ohlcv(symbol, timeframe=timeframe, limit=LIMIT)
        
        if not candles_data:
            print("No data returned")
            return 0
        
        async with Database.get_session() as session:
            count = 0
            for c in candles_data:
                candle_db = Candle(
                    symbol=symbol,
                    provider=provider.name,
                    timeframe=timeframe,
                    timestamp=c.timestamp,
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume
                )
                await session.merge(candle_db)
                count += 1
            
            await session.commit()
        
        print(f"{count} candles saved")
        return count
        
    except Exception as e:
        print(f"Error: {e}")
        return 0

async def main():
    print("=" * 60)
    print("Argus Historical Data Backfill")
    print(f"Provider: {PROVIDER_NAME}")
    print(f"Symbols: {', '.join(SYMBOLS)}")
    print(f"Timeframes: {', '.join(TIMEFRAMES)}")
    print(f"Max candles per pair: {LIMIT}")
    print("=" * 60)
    
    # Initialize
    Database.init()
    await Database.create_tables()

    if PROVIDER_NAME == "okx":
        provider = OKXProvider()
    else:
        provider = BinanceProvider()
    
    total_candles = 0
    total_pairs = len(SYMBOLS) * len(TIMEFRAMES)
    current = 0
    
    try:
        for symbol in SYMBOLS:
            print(f"\nProcessing {symbol}...")
            
            for timeframe in TIMEFRAMES:
                current += 1
                print(f"  [{current}/{total_pairs}]", end=" ")
                
                count = await backfill_candles(provider, symbol, timeframe)
                total_candles += count
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.5)
    
    finally:
        await provider.close()
        await Database.close()
    
    print("\n" + "=" * 60)
    print(f"Backfill Complete!")
    print(f"   Provider: {PROVIDER_NAME}")
    print(f"   Total candles stored: {total_candles:,}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
