"""
Snapshot Worker Job
===================
snapshot_signal_outcomes — daily at 00:05 UTC — aggregate resolved signal_log
rows into daily win-rate snapshots by (regime, conviction_band, source, coin).

Idempotent: if today's aggregate sentinel row already exists the job returns
early without doing any work, making it safe to re-run or retry.
"""
import logging
from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.storage import Database
from app.schemas.signal_log import SignalLog
from app.schemas.snapshot import SignalOutcomeSnapshot

logger = logging.getLogger(__name__)

# Conviction band boundaries (lower-inclusive)
def _conviction_band(conviction: int) -> str:
    if conviction >= 75:
        return "75+"
    if conviction >= 65:
        return "65-74"
    return "55-64"


async def snapshot_signal_outcomes(ctx):  # noqa: C901  (complexity acceptable for a batch job)
    """
    Aggregate resolved SignalLog rows into SignalOutcomeSnapshot daily rows.

    Dimensions:
      - Every (regime, conviction_band, source, coin) combo observed today
      - Plus "ALL" rollup rows for each dimension individually and the grand total

    Idempotency guard: checks for the grand-total sentinel row
    (regime=ALL, conviction_band=ALL, source=ALL, coin IS NULL) before doing
    any work.
    """
    snapshot_date = datetime.utcnow().date().isoformat()

    async with Database.get_session() as session:
        # ------------------------------------------------------------------
        # Idempotency: skip if sentinel row already exists
        # ------------------------------------------------------------------
        sentinel = await session.execute(
            select(SignalOutcomeSnapshot).where(
                SignalOutcomeSnapshot.snapshot_date == snapshot_date,
                SignalOutcomeSnapshot.regime == "ALL",
                SignalOutcomeSnapshot.conviction_band == "ALL",
                SignalOutcomeSnapshot.source == "ALL",
                SignalOutcomeSnapshot.coin.is_(None),
            )
        )
        if sentinel.scalars().first() is not None:
            logger.info(f"snapshot_signal_outcomes: sentinel for {snapshot_date} already exists — skipping")
            return

        # ------------------------------------------------------------------
        # Fetch all resolved signals
        # ------------------------------------------------------------------
        result = await session.execute(
            select(SignalLog).where(
                SignalLog.outcome.in_(["WIN", "LOSS", "REVIEW", "REJECTED"])
            )
        )
        signals = result.scalars().all()

        if not signals:
            logger.info(f"snapshot_signal_outcomes: no resolved signals found for {snapshot_date}")

        # ------------------------------------------------------------------
        # Accumulate counts per (regime, conviction_band, source, coin)
        # ------------------------------------------------------------------
        # Each bucket: {"wins": 0, "losses": 0, "reviews": 0, "rejected": 0, "times": []}
        Bucket = lambda: {"wins": 0, "losses": 0, "reviews": 0, "rejected": 0, "times": []}
        buckets: dict = defaultdict(Bucket)

        for sig in signals:
            regime = sig.regime_at_signal or sig.market_state or "UNKNOWN"
            band = _conviction_band(sig.conviction)
            source = sig.source or "live"
            coin = sig.symbol  # e.g. "BTCUSDT"
            outcome = sig.outcome

            # Time-to-resolution (ms) — only when both timestamps available
            ttr = None
            if sig.resolved_at is not None and sig.fired_at is not None:
                ttr = sig.resolved_at - sig.fired_at

            def _record(key, ttr_val):
                b = buckets[key]
                if outcome == "WIN":
                    b["wins"] += 1
                elif outcome == "LOSS":
                    b["losses"] += 1
                elif outcome == "REVIEW":
                    b["reviews"] += 1
                elif outcome == "REJECTED":
                    b["rejected"] += 1
                if ttr_val is not None:
                    b["times"].append(ttr_val)

            # Exact slice
            _record((regime, band, source, coin), ttr)
            # Source rollup (coin-level)
            _record((regime, band, "ALL", coin), ttr)
            # Band rollup (coin-level)
            _record((regime, "ALL", source, coin), ttr)
            # Regime rollup (coin-level)
            _record(("ALL", band, source, coin), ttr)
            # All-source + all-band (coin-level)
            _record((regime, "ALL", "ALL", coin), ttr)
            _record(("ALL", band, "ALL", coin), ttr)
            _record(("ALL", "ALL", source, coin), ttr)
            # Grand total per coin
            _record(("ALL", "ALL", "ALL", coin), ttr)

            # Aggregate (no-coin) versions of all above
            _record((regime, band, source, None), ttr)
            _record((regime, band, "ALL", None), ttr)
            _record((regime, "ALL", source, None), ttr)
            _record(("ALL", band, source, None), ttr)
            _record((regime, "ALL", "ALL", None), ttr)
            _record(("ALL", band, "ALL", None), ttr)
            _record(("ALL", "ALL", source, None), ttr)
            # Grand total sentinel
            _record(("ALL", "ALL", "ALL", None), ttr)

        # ------------------------------------------------------------------
        # Upsert all buckets
        # ------------------------------------------------------------------
        rows_written = 0
        for (regime, band, source, coin), b in buckets.items():
            wins = b["wins"]
            losses = b["losses"]
            reviews = b["reviews"]
            rejected = b["rejected"]
            total_resolved = wins + losses + reviews + rejected
            win_rate = round(wins / (wins + losses) * 100, 2) if (wins + losses) > 0 else None
            times = b["times"]
            avg_ttr = round(sum(times) / len(times), 2) if times else None

            row = {
                "snapshot_date": snapshot_date,
                "regime": regime,
                "conviction_band": band,
                "source": source,
                "coin": coin,
                "wins": wins,
                "losses": losses,
                "reviews": reviews,
                "rejected": rejected,
                "total_resolved": total_resolved,
                "win_rate": win_rate,
                "avg_time_to_resolution_ms": avg_ttr,
                "created_at": datetime.utcnow(),
            }

            # Choose the right conflict target based on whether coin is NULL
            if coin is None:
                stmt = (
                    pg_insert(SignalOutcomeSnapshot)
                    .values(**row)
                    .on_conflict_do_update(
                        index_elements=["snapshot_date", "regime", "conviction_band", "source"],
                        index_where=SignalOutcomeSnapshot.__table__.c.coin.is_(None),
                        set_={k: row[k] for k in (
                            "wins", "losses", "reviews", "rejected",
                            "total_resolved", "win_rate", "avg_time_to_resolution_ms",
                        )},
                    )
                )
            else:
                stmt = (
                    pg_insert(SignalOutcomeSnapshot)
                    .values(**row)
                    .on_conflict_do_update(
                        index_elements=["snapshot_date", "regime", "conviction_band", "source", "coin"],
                        index_where=SignalOutcomeSnapshot.__table__.c.coin.isnot(None),
                        set_={k: row[k] for k in (
                            "wins", "losses", "reviews", "rejected",
                            "total_resolved", "win_rate", "avg_time_to_resolution_ms",
                        )},
                    )
                )

            await session.execute(stmt)
            rows_written += 1

        await session.commit()

    logger.info(
        f"snapshot_signal_outcomes: {snapshot_date} — {len(signals)} signals → "
        f"{rows_written} snapshot rows upserted"
    )
