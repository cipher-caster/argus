"""
v0.9.2 Schema Migration
Adds provider column to position table to track which data provider was used
when the position was opened, so candle resolution always uses the correct source.

Run inside Docker:
  docker compose exec -e PYTHONPATH=/app/backend python migrate_v0_9_2.py
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALTERS = [
    "ALTER TABLE position ADD COLUMN IF NOT EXISTS provider VARCHAR DEFAULT 'binance'",
    "UPDATE position SET provider = 'binance' WHERE provider IS NULL",
]


async def migrate():
    from app.storage import Database
    from sqlalchemy import text

    async with Database.get_session() as session:
        for sql in ALTERS:
            await session.execute(text(sql))
        await session.commit()

    logger.info("v0.9.2 migration complete — provider column added to position")


if __name__ == "__main__":
    asyncio.run(migrate())
