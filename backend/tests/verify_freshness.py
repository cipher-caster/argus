import asyncio

import pandas as pd

from app.routes.strategy import get_candles_df
from app.schemas.candle import Candle as DbCandle
from app.storage import Database


async def verify():
    await Database.init()
    await Database.create_tables()

    symbol = "BTC/USDT"
    timeframe = "1h"

    # 1. Insert a STALE candle (e.g. 5 hours ago)
    async with Database.get_session() as session:
        # Clear existing
        # await session.execute("DELETE FROM candle WHERE symbol='BTC/USDT' AND timeframe='1h'")
        # ... proper SQLAlchemy delete ...
        from sqlmodel import delete

        statement = delete(DbCandle).where(
            DbCandle.symbol == symbol, DbCandle.timeframe == timeframe
        )
        await session.execute(statement)

        # Insert stale
        stale_ts = int(pd.Timestamp.now().timestamp() - 5 * 3600) * 1000  # 5 hours ago
        c = DbCandle(
            symbol=symbol,
            provider="binance",
            timeframe=timeframe,
            timestamp=stale_ts,
            open=100000,
            high=100000,
            low=100000,
            close=100000,
            volume=100,
        )
        session.add(c)
        await session.commit()
        print(f"Inserted stale candle at {pd.to_datetime(stale_ts, unit='ms')}")

    # 2. Call get_candles_df
    print("Calling get_candles_df...")
    df = await get_candles_df(symbol, timeframe, limit=10)

    if df.empty:
        print("FAILED: Returned empty DataFrame")
        return

    latest_ts = df.iloc[-1]["timestamp"]
    print(f"Latest candle timestamp: {latest_ts}")

    latest_ts_ms = latest_ts.timestamp() * 1000
    now_ms = pd.Timestamp.now().timestamp() * 1000
    diff_hours = (now_ms - latest_ts_ms) / 1000 / 3600

    print(f"Diff hours: {diff_hours:.2f}")

    if diff_hours < 2.0:
        print("SUCCESS: Data is FRESH (fetched from Binance)")
    else:
        print("FAILURE: Data is still STALE (served from DB)")


if __name__ == "__main__":
    asyncio.run(verify())
