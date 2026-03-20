"""
v0.9.1 Schema Migration
Adds new columns to signal_log and position tables for learning from trades.

Run inside Docker:
  docker compose exec -e PYTHONPATH=/app/backend python migrate_v0_9_1.py
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALTERS = [
    "ALTER TABLE signal_log ADD COLUMN IF NOT EXISTS regime_at_resolution VARCHAR",
    "ALTER TABLE signal_log ADD COLUMN IF NOT EXISTS btc_price_at_resolution FLOAT",
    "ALTER TABLE signal_log ADD COLUMN IF NOT EXISTS time_to_resolution_ms BIGINT",
    "ALTER TABLE signal_log ADD COLUMN IF NOT EXISTS rejection_reason VARCHAR",
    "ALTER TABLE position ADD COLUMN IF NOT EXISTS market_state_at_close VARCHAR",
]


async def migrate():
    from app.storage import Database
    from sqlalchemy import text

    async with Database.get_session() as session:
        for sql in ALTERS:
            await session.execute(text(sql))
        await session.commit()

    logger.info("v0.9.1 migration complete — new columns added to signal_log and position")


if __name__ == "__main__":
    asyncio.run(migrate())
