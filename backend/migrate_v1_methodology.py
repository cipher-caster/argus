"""
v1_methodology Schema Migration — adds methodology_version column to signal_log.

Existing rows (legacy, pre-P0-fix) are tagged v1.
New rows default to v2.

Run inside Docker:
  docker compose exec -e PYTHONPATH=/app/backend python migrate_v1_methodology.py
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALTERS = [
    # Add column — server_default='v1' so existing rows immediately get v1
    "ALTER TABLE signal_log ADD COLUMN IF NOT EXISTS methodology_version VARCHAR(8) NOT NULL DEFAULT 'v1'",
    # Index for fast v2-only filtering
    "CREATE INDEX IF NOT EXISTS ix_signal_log_methodology_version ON signal_log (methodology_version)",
]


async def migrate():
    from app.storage import Database
    from sqlalchemy import text

    Database.init()
    async with Database.get_session() as session:
        for sql in ALTERS:
            await session.execute(text(sql))
        await session.commit()

    logger.info(
        "v1_methodology migration complete — methodology_version column added; "
        "all existing rows tagged v1"
    )


if __name__ == "__main__":
    asyncio.run(migrate())
