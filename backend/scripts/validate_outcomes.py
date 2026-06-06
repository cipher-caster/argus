"""
Validate signal/position outcome consistency.
Run after fix_historical_data.py to confirm everything is correct.
"""
import asyncio
import sys

sys.path.insert(0, "/app")

from app.storage import Database
from sqlmodel import text


async def run():
    Database.init()
    async with Database.get_session() as session:
        print("=== POSITION VALIDATION ===\n")

        # 1. WIN with negative PnL
        r = await session.execute(
            text("""
            SELECT id, symbol, direction, outcome, pnl_usd
            FROM position WHERE status='CLOSED' AND outcome='WIN' AND pnl_usd < 0
        """)
        )
        bad_win = r.fetchall()
        print(f"WIN with negative PnL: {len(bad_win)}")
        for b in bad_win:
            print(f"  #{b[0]} {b[1]} {b[2]} pnl={b[4]}")

        # 2. LOSS with positive PnL
        r = await session.execute(
            text("""
            SELECT id, symbol, direction, outcome, pnl_usd
            FROM position WHERE status='CLOSED' AND outcome='LOSS' AND pnl_usd > 0
        """)
        )
        bad_loss = r.fetchall()
        print(f"LOSS with positive PnL: {len(bad_loss)}")
        for b in bad_loss:
            print(f"  #{b[0]} {b[1]} {b[2]} pnl={b[4]}")

        # 3. Overall stats
        r = await session.execute(
            text("""
            SELECT outcome, COUNT(*), ROUND(AVG(pnl_usd)::numeric, 2), ROUND(SUM(pnl_usd)::numeric, 2)
            FROM position WHERE status='CLOSED'
            GROUP BY outcome
        """)
        )
        print(f"\n--- Position Stats ---")
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]} trades, avg={row[2]}, total={row[3]}")

        # 4. Signal-Position mismatches (informational only)
        r = await session.execute(
            text("""
            SELECT sl.id, sl.symbol, sl.outcome as sig_outcome,
                   p.outcome as pos_outcome, p.pnl_usd
            FROM signal_log sl
            JOIN position p ON p.signal_log_id = sl.id
            WHERE p.status = 'CLOSED'
              AND sl.outcome != 'OPEN' AND sl.outcome != 'REJECTED'
              AND sl.outcome != p.outcome
        """)
        )
        mismatches = r.fetchall()
        print(f"\n--- Signal-Position Outcome Mismatches (informational) ---")
        print(f"Total mismatches: {len(mismatches)}")
        for m in mismatches:
            print(f"  Signal #{m[0]} {m[1]}: sig={m[2]} pos={m[3]} pnl={m[4]}")

        # 5. Summary
        has_errors = len(bad_win) > 0 or len(bad_loss) > 0
        print(
            f"\n{'PASS' if not has_errors else 'FAIL'}: Outcome validation "
            f"{'passed' if not has_errors else 'failed'}"
        )


if __name__ == "__main__":
    asyncio.run(run())
