"""
v0.19.0 Schema Migration — creates signal_outcome_snapshot table (Phase 19).

Run inside Docker:
  docker compose exec -e PYTHONPATH=/app/backend python migrate_v0_19_0.py
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS signal_outcome_snapshot (
    id                        SERIAL PRIMARY KEY,
    snapshot_date             VARCHAR NOT NULL,
    regime                    VARCHAR NOT NULL,
    conviction_band           VARCHAR NOT NULL,
    source                    VARCHAR NOT NULL,
    coin                      VARCHAR,
    wins                      INTEGER NOT NULL DEFAULT 0,
    losses                    INTEGER NOT NULL DEFAULT 0,
    reviews                   INTEGER NOT NULL DEFAULT 0,
    rejected                  INTEGER NOT NULL DEFAULT 0,
    total_resolved            INTEGER NOT NULL DEFAULT 0,
    win_rate                  FLOAT,
    avg_time_to_resolution_ms FLOAT,
    created_at                TIMESTAMP NOT NULL DEFAULT NOW()
)
"""

# Partial unique index for aggregate rows (coin IS NULL)
CREATE_INDEX_AGGREGATE = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_snapshot_aggregate
    ON signal_outcome_snapshot (snapshot_date, regime, conviction_band, source)
    WHERE coin IS NULL
"""

# Partial unique index for per-coin rows (coin IS NOT NULL)
CREATE_INDEX_PER_COIN = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_snapshot_per_coin
    ON signal_outcome_snapshot (snapshot_date, regime, conviction_band, source, coin)
    WHERE coin IS NOT NULL
"""

STATEMENTS = [CREATE_TABLE, CREATE_INDEX_AGGREGATE, CREATE_INDEX_PER_COIN]


async def migrate():
    from app.storage import Database
    from sqlalchemy import text

    async with Database.get_session() as session:
        for sql in STATEMENTS:
            await session.execute(text(sql))
        await session.commit()

    logger.info("v0.19.0 migration complete — signal_outcome_snapshot table created")


if __name__ == "__main__":
    asyncio.run(migrate())
