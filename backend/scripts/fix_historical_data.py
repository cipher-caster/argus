"""
Fix historical position outcomes and PnL calculations.

Bug: The historical resolution path (signal_log.py line 686) copied signal
outcome to position outcome regardless of actual PnL. The fee formula also
differed between fast-path and historical resolution.

This script:
1. Recalculates PnL for all CLOSED positions using consistent fee formula
2. Sets outcome based on actual PnL (WIN if pnl_usd >= 0, else LOSS)
3. Fixes trade events to match corrected outcomes
"""
import asyncio
import sys
import argparse

sys.path.insert(0, "/app")

from app.storage import Database
from sqlmodel import text

FEE_PCT = 0.001


async def run(dry_run: bool = True):
    Database.init()
    async with Database.get_session() as session:
        # 1. Fetch all CLOSED positions with PnL
        result = await session.execute(text("""
            SELECT id, symbol, direction, status, actual_entry, intended_entry,
                   actual_exit, intended_tp, intended_sl, quantity, quote_amount,
                   pnl_usd, pnl_pct, outcome, signal_log_id
            FROM position
            WHERE status = 'CLOSED'
            ORDER BY closed_at DESC
        """))
        rows = result.fetchall()

        changes = []
        for row in rows:
            (pos_id, symbol, direction, status, actual_entry, intended_entry,
             actual_exit, intended_tp, intended_sl, quantity, quote_amount,
             old_pnl_usd, old_pnl_pct, old_outcome, signal_log_id) = row

            entry = actual_entry or intended_entry
            exit_price = actual_exit

            if not entry or not exit_price or not quantity:
                continue

            # Recalculate PnL with consistent fee
            if direction == "LONG":
                raw_pnl = (exit_price - entry) * quantity
            else:
                raw_pnl = (entry - exit_price) * quantity

            fee = quote_amount * FEE_PCT
            new_pnl_usd = round(raw_pnl - fee, 4)
            new_pnl_pct = (
                round((new_pnl_usd / quote_amount * 100), 2)
                if quote_amount > 0
                else 0.0
            )
            new_outcome = "WIN" if new_pnl_usd >= 0 else "LOSS"

            # Check if outcome or PnL needs fixing
            outcome_changed = old_outcome != new_outcome
            pnl_changed = (
                old_pnl_usd is None
                or round(old_pnl_usd, 4) != new_pnl_usd
            )

            if outcome_changed or pnl_changed:
                changes.append(
                    {
                        "pos_id": pos_id,
                        "symbol": symbol,
                        "direction": direction,
                        "old_outcome": old_outcome,
                        "new_outcome": new_outcome,
                        "old_pnl_usd": old_pnl_usd,
                        "new_pnl_usd": new_pnl_usd,
                        "old_pnl_pct": old_pnl_pct,
                        "new_pnl_pct": new_pnl_pct,
                        "entry": entry,
                        "exit": exit_price,
                        "quote_amount": quote_amount,
                    }
                )

        if not changes:
            print("No changes needed. All position outcomes are correct.")
            return

        print(f"\n{'=' * 80}")
        print(f"Found {len(changes)} positions to fix:")
        print(f"{'=' * 80}\n")

        for c in changes:
            flag = (
                " *** OUTCOME FLIP ***"
                if c["old_outcome"] != c["new_outcome"]
                else ""
            )
            print(f"  Position #{c['pos_id']} ({c['symbol']} {c['direction']}){flag}")
            print(f"    Outcome:  {c['old_outcome']} -> {c['new_outcome']}")
            print(f"    PnL USD:  {c['old_pnl_usd']} -> {c['new_pnl_usd']}")
            print(f"    PnL %:    {c['old_pnl_pct']}% -> {c['new_pnl_pct']}%")
            print(
                f"    Entry:    {c['entry']}  Exit: {c['exit']}  Quote: {c['quote_amount']}"
            )
            print()

        if dry_run:
            print(
                "DRY RUN -- no changes applied. Run without --dry-run to commit."
            )
            return

        # 2. Apply position fixes
        for c in changes:
            await session.execute(
                text("""
                UPDATE position
                SET outcome = :outcome,
                    pnl_usd = :pnl_usd,
                    pnl_pct = :pnl_pct
                WHERE id = :pos_id
            """),
                {
                    "outcome": c["new_outcome"],
                    "pnl_usd": c["new_pnl_usd"],
                    "pnl_pct": c["new_pnl_pct"],
                    "pos_id": c["pos_id"],
                },
            )

        # 3. Fix trade events for flipped outcomes
        outcome_flip_ids = [
            c["pos_id"]
            for c in changes
            if c["old_outcome"] != c["new_outcome"]
        ]
        if outcome_flip_ids:
            # Fix TP_HIT -> SL_HIT for positions that flipped WIN->LOSS
            win_to_loss = [
                c["pos_id"]
                for c in changes
                if c["old_outcome"] == "WIN" and c["new_outcome"] == "LOSS"
            ]
            if win_to_loss:
                await session.execute(
                    text("""
                    UPDATE trade_event
                    SET event_type = 'SL_HIT'
                    WHERE position_id = ANY(:ids) AND event_type = 'TP_HIT'
                """),
                    {"ids": win_to_loss},
                )
                print(
                    f"Fixed {len(win_to_loss)} trade events: TP_HIT -> SL_HIT"
                )

            # Fix SL_HIT -> TP_HIT for positions that flipped LOSS->WIN
            loss_to_win = [
                c["pos_id"]
                for c in changes
                if c["old_outcome"] == "LOSS" and c["new_outcome"] == "WIN"
            ]
            if loss_to_win:
                await session.execute(
                    text("""
                    UPDATE trade_event
                    SET event_type = 'TP_HIT'
                    WHERE position_id = ANY(:ids) AND event_type = 'SL_HIT'
                """),
                    {"ids": loss_to_win},
                )
                print(
                    f"Fixed {len(loss_to_win)} trade events: SL_HIT -> TP_HIT"
                )

        await session.commit()
        print(f"\nApplied {len(changes)} position fixes successfully.")

        # 4. Verification
        verify = await session.execute(
            text("""
            SELECT id, symbol, outcome, pnl_usd
            FROM position
            WHERE status = 'CLOSED'
              AND ((outcome = 'WIN' AND pnl_usd < 0) OR (outcome = 'LOSS' AND pnl_usd > 0))
        """)
        )
        bad = verify.fetchall()
        if bad:
            print(
                f"\nWARNING: {len(bad)} positions still have mismatched outcome/PnL!"
            )
            for b in bad:
                print(f"  #{b[0]} {b[1]} outcome={b[2]} pnl={b[3]}")
        else:
            print(
                "\nVerification passed: all position outcomes match their PnL."
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()
    asyncio.run(run(dry_run=args.dry_run))
