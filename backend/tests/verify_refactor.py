import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.market_data import MarketDataService
from app.storage import Database


async def verify():
    print("Initializing DB...")
    Database.init()

    symbol = "BTC/USDT"
    timeframe = "1h"
    limit = 10

    print(f"Fetching OHLCV for {symbol} {timeframe}...")
    try:
        candles, provider = await MarketDataService.fetch_and_sync_ohlcv(symbol, timeframe, limit)
        print(f"Success! Provider: {provider}")
        print(f"Candles: {len(candles)}")
        if candles:
            print(f"First Candle: {candles[0]}")
            print(f"Last Candle: {candles[-1]}")
    except Exception as e:
        print(f"Error fetching OHLCV: {e}")
        import traceback

        traceback.print_exc()

    print("\nTesting Coin Filter/Sort...")
    # Mock data
    raw_data = [
        {"symbol": "BTC/USDT", "price": 50000, "market_cap": 1000000, "name": "Bitcoin"},
        {"symbol": "ETH/USDT", "price": 3000, "market_cap": 500000, "name": "Ethereum"},
        {"symbol": "DOGE/USDT", "price": 0.1, "market_cap": 10000, "name": "Dogecoin"},
    ]

    coins, total = MarketDataService.filter_and_sort_coins(
        raw_data, sort_by="market_cap", sort_order="desc"
    )
    print(f"Total Coins: {total}")
    print(f"Top Coin: {coins[0].symbol} (Rank {coins[0].rank})")

    if coins[0].symbol == "BTC/USDT":
        print("Sorting Success")
    else:
        print("Sorting Failed")


if __name__ == "__main__":
    asyncio.run(verify())
