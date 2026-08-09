#!/usr/bin/env python3
"""
Signal Backtest Script — Oracle + Titan on 4H
====================================================
Replays the Oracle + Titan combined setup logic over historical candles.
Writes results to signal_log (source='backtest') and prints observations.

Usage (inside Docker):
    docker compose exec backend python scripts/run_signal_backtest.py
    docker compose exec backend python scripts/run_signal_backtest.py --symbols=TAO,LINK --dry-run --fix-optimal
    docker compose exec backend python scripts/run_signal_backtest.py --provider=okx --symbols=BTC,ETH

Flags:
    --provider=X    Data source: 'binance' (default) or 'okx'
    --symbols=X,Y   Comma-separated coins to test (default: all watchlist coins)
    --dry-run       Print signals without writing to DB
    --clear         Delete existing backtest rows before running
    --fix-optimal   Apply all proven optimizations (BLOCK_SLEEPING + FIXED_TP_2.0x + SOFT_MACRO)

Experiment flags:
    --fix-sleeping     Block SLEEPING market state
    --fix-tp           Use adaptive TP (2× ATR normal, 3× only SUPER TREND) [legacy]
    --fix-soft-macro   Soft macro guard (block worst counter-trend)
    --fix-macro        Strict macro alignment
    --fix-all          All fixes (strict macro)
    --sl-mult=X        SL multiplier (default: 1.5× ATR). Try 1.0, 1.25, 2.0
    --tp-mult=X        TP multiplier override (default: 2.0/3.0 adaptive)
    --min-conv=X       Min Titan confidence (default: 55)

Known limitations:
    - SMC indicators (MSS, sweeps, FVGs) are pre-computed on the full dataset.
      This may introduce slight look-ahead for those specific signals.
    - Outcome resolution checks if candle HIGH >= TP or LOW <= SL.
      In a same-candle hit (both TP and SL touched), LOSS is assumed (conservative).
"""

import asyncio
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.constants import active_provider_name
from app.storage import Database
from app.schemas.signal_log import SignalLog
from app.trading.backtest_engine import (
    BacktestConfig,
    DEFAULT_COINS,
    load_and_prepare_data,
    backtest_symbol,
    compute_stats,
)

# ---------------------------------------------------------------------------
# CLI arg parsing
# ---------------------------------------------------------------------------

def _parse_flag(prefix, default):
    for arg in sys.argv:
        if arg.startswith(prefix):
            return float(arg.split("=")[1])
    return default


def _parse_symbols() -> list[str]:
    for arg in sys.argv:
        if arg.startswith("--symbols="):
            return [c.strip().upper() for c in arg.split("=")[1].split(",") if c.strip()]
    return list(DEFAULT_COINS)


def _parse_provider() -> str:
    for arg in sys.argv:
        if arg.startswith("--provider="):
            return arg.split("=")[1].strip().lower()
    return active_provider_name()


DRY_RUN = "--dry-run" in sys.argv
CLEAR_EXISTING = "--clear" in sys.argv

FIX_OPTIMAL = "--fix-optimal" in sys.argv
FIX_ALL = "--fix-all" in sys.argv

config = BacktestConfig(
    symbols=_parse_symbols(),
    provider=_parse_provider(),
    sl_mult=_parse_flag("--sl-mult=", 1.5),
    tp_mult=_parse_flag("--tp-mult=", 2.0),
    tp_adaptive="--fix-tp" in sys.argv or FIX_ALL,
    min_titan_confidence=int(_parse_flag("--min-conv=", 55)),
    block_sleeping="--fix-sleeping" in sys.argv or FIX_ALL or FIX_OPTIMAL,
    block_volatile=True,
    macro_guard="--fix-soft-macro" in sys.argv or FIX_OPTIMAL,
    strict_macro="--fix-macro" in sys.argv or FIX_ALL,
)


# ---------------------------------------------------------------------------
# CLI reporter (rich output, not in engine)
# ---------------------------------------------------------------------------

def print_observations(all_signals: list, cfg: BacktestConfig):
    print("\n" + "=" * 70)
    print("BACKTEST OBSERVATIONS")
    print("=" * 70)

    if not all_signals:
        print("  No signals fired. Possible reasons:")
        print("  - Oracle + Titan rarely agree at conviction threshold")
        print("  - Market gate filtered out most candles")
        print("  - Insufficient warmup data")
        return

    stats = compute_stats(all_signals)

    tp_label = "adaptive" if cfg.tp_adaptive and cfg.tp_mult == 0 else f"{cfg.tp_mult}×ATR"
    print(f"\n  OVERALL: {stats['total']} signals | "
          f"{stats['wins']}W {stats['losses']}L {stats['reviews']}R | "
          f"Win Rate: {stats['win_rate']}% (break-even = 33.3%)")
    print(f"  Total Profit: {stats['total_r']:+.1f}R | Avg RR: {stats['avg_rr']:.2f}:1")
    print(f"  Settings: SL={cfg.sl_mult}×ATR | TP={tp_label} | MinConf={cfg.min_titan_confidence}%")

    # Direction breakdown
    longs_all = [s for s in all_signals if s["direction"] == "LONG"]
    shorts_all = [s for s in all_signals if s["direction"] == "SHORT"]
    for label, subset in [("LONGS", longs_all), ("SHORTS", shorts_all)]:
        if not subset:
            continue
        w = sum(1 for s in subset if s["outcome"] == "WIN")
        l = sum(1 for s in subset if s["outcome"] == "LOSS")
        cl = w + l
        wr = round(w / cl * 100, 1) if cl > 0 else "N/A"
        print(f"  {label}: {len(subset)} signals, {wr}% WR")

    for symbol, coin_stats in sorted(stats["coin_results"].items()):
        sigs = [s for s in all_signals if s["symbol"] == symbol]
        longs = [s for s in sigs if s["direction"] == "LONG"]
        shorts = [s for s in sigs if s["direction"] == "SHORT"]

        print(f"\n  {symbol}:")
        print(f"    Total signals : {coin_stats['total']} ({len(longs)} LONG, {len(shorts)} SHORT)")
        print(f"    Win/Loss/Review: {coin_stats['wins']}/{coin_stats['losses']}/{coin_stats['reviews']}")
        print(f"    Win Rate       : {coin_stats['win_rate']}%")
        print(f"    Profit         : {coin_stats['profit_r']:+.1f}R")

        high_conv = [s for s in sigs if s["conviction"] >= 70]
        low_conv = [s for s in sigs if s["conviction"] < 70]
        if high_conv:
            hc_wins = sum(1 for s in high_conv if s["outcome"] == "WIN")
            hc_cl = sum(1 for s in high_conv if s["outcome"] in ("WIN", "LOSS"))
            hc_wr = round(hc_wins / hc_cl * 100, 1) if hc_cl > 0 else None
            print(f"    High conv (>=70): {len(high_conv)} signals, {hc_wr}% WR")
        if low_conv:
            lc_wins = sum(1 for s in low_conv if s["outcome"] == "WIN")
            lc_cl = sum(1 for s in low_conv if s["outcome"] in ("WIN", "LOSS"))
            lc_wr = round(lc_wins / lc_cl * 100, 1) if lc_cl > 0 else None
            print(f"    Low conv (<70) : {len(low_conv)} signals, {lc_wr}% WR")

        by_state = defaultdict(list)
        for s in sigs:
            by_state[s["market_state"]].append(s)
        print(f"    By market state:")
        for state, state_sigs in sorted(by_state.items()):
            s_wins = sum(1 for s in state_sigs if s["outcome"] == "WIN")
            s_cl = sum(1 for s in state_sigs if s["outcome"] in ("WIN", "LOSS"))
            s_wr = round(s_wins / s_cl * 100, 1) if s_cl > 0 else "N/A"
            print(f"      {state:15s}: {len(state_sigs)} signals, {s_wr}% WR")

    print("\n  NOTES:")
    print("  - REVIEW = signal open after 7 days (42×4H candles), neither TP nor SL hit")
    print("  - SMC components (MSS/sweeps/FVG) pre-computed on full dataset — minor look-ahead possible")
    print("  - Same-candle TP+SL hit resolved as LOSS (conservative assumption)")
    print("  - Market gate: skipped VOLATILE candles and BTC SELL/STRONG_SELL bars")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    print("=" * 70)
    print(f"Argus Signal Backtest — {', '.join(config.symbols)} (4H) [{config.provider}]")
    print(f"Config: {config.name}")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'WRITE TO DB'}")
    print("=" * 70)

    Database.init()
    await Database.create_tables()

    if CLEAR_EXISTING and not DRY_RUN:
        print("\nClearing existing backtest rows...")
        async with Database.get_session() as session:
            from sqlalchemy import delete
            await session.execute(delete(SignalLog).where(SignalLog.source == "backtest"))
            await session.commit()
        print("  Done.")

    print("\nLoading candle data...")
    data = await load_and_prepare_data(config.symbols, provider=config.provider)

    all_signals = []
    for coin in config.symbols:
        coin_data = data["coin_data"].get(coin, {})
        df_4h = coin_data.get("4h")
        df_1d = coin_data.get("1d")
        if df_4h is None or df_1d is None:
            print(f"  [{coin}] No data — skipping")
            continue
        sigs = await backtest_symbol(
            f"{coin}/USDT", df_4h, df_1d,
            data["btc_4h"], data["btc_macro_biases"],
            config,
        )
        all_signals.extend(sigs)

    print_observations(all_signals, config)

    if not DRY_RUN and all_signals:
        print(f"\nWriting {len(all_signals)} signals to signal_log...")
        async with Database.get_session() as session:
            for sig in all_signals:
                session.add(SignalLog(**sig))
            await session.commit()
        print(f"  Done. View in Analytics → Signal Log (filter: Backtest)")
    elif DRY_RUN:
        print("\nDry run — nothing written to DB.")

    await Database.close()


if __name__ == "__main__":
    asyncio.run(main())
