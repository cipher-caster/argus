"""
v0.9.3 Schema Migration — adds entry-time regime context to signal_log (Phase 18 closeout).

Run inside Docker:
  docker compose exec -e PYTHONPATH=/app/backend python migrate_v0_9_3.py
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALTERS = [
    "ALTER TABLE signal_log ADD COLUMN IF NOT EXISTS regime_at_signal VARCHAR",
    "ALTER TABLE signal_log ADD COLUMN IF NOT EXISTS btc_price_at_signal FLOAT",
]


async def migrate():
    from app.storage import Database
    from sqlalchemy import text

    async with Database.get_session() as session:
        for sql in ALTERS:
            await session.execute(text(sql))
        await session.commit()

    logger.info("v0.9.3 migration complete — entry-time regime context added to signal_log")


if __name__ == "__main__":
    asyncio.run(migrate())
