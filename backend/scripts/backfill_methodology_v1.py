"""
One-shot backfill: tag all rows that predate the methodology_version column as v1.

Run AFTER migrate_v1_methodology.py has added the column.

Usage (inside Docker):
  docker compose exec -e PYTHONPATH=/app/backend python scripts/backfill_methodology_v1.py

Safe to run multiple times — only updates rows that are not already v2.
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def backfill():
    from app.storage import Database
    from sqlalchemy import text

    Database.init()
    async with Database.get_session() as session:
        result = await session.execute(
            text(
                "UPDATE signal_log SET methodology_version = 'v1' "
                "WHERE methodology_version IS NULL OR methodology_version != 'v2'"
            )
        )
        await session.commit()
        logger.info(f"Backfill complete — {result.rowcount} row(s) tagged v1")


if __name__ == "__main__":
    asyncio.run(backfill())
