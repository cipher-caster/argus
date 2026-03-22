#!/usr/bin/env python3
"""
OKX Backtest — Backfill + Backtest Pipeline
Fetches historical OHLCV from OKX, stores in DB, runs the backtest engine.

Usage:
    docker compose exec backend python scripts/okx_backtest.py
    docker compose exec backend python scripts/okx_backtest.py --symbols=BTC,ETH,SOL
    docker compose exec backend python scripts/okx_backtest.py --dry-run --sl-mult=2.0
    docker compose exec backend python scripts/okx_backtest.py --skip-backfill   # reuse existing OKX data
"""

import asyncio
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.storage import Database
from app.providers.okx_provider import OKXProvider
from app.schemas.candle import Candle as DbCandle
from app.trading.backtest_engine import (
    BacktestConfig,
    load_and_prepare_data,
    backtest_symbol,
    compute_stats,
)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _flag(prefix, default=None):
    for arg in sys.argv:
        if arg.startswith(prefix):
            return arg.split("=", 1)[1]
    return default


def _parse_symbols() -> list[str]:
    raw = _flag("--symbols=")
    if raw:
        return [s.strip().upper() for s in raw.split(",") if s.strip()]
    # Custom starter list — coins likely available on OKX spot
    return ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "DOT", "LINK", "ARB"]


DRY_RUN = "--dry-run" in sys.argv
SKIP_BACKFILL = "--skip-backfill" in sys.argv
SL_MULT = float(_flag("--sl-mult=", "1.5"))
MIN_CONF = int(_flag("--min-conv=", "55"))

SYMBOLS = _parse_symbols()
TIMEFRAMES = ["4h", "1d"]  # minimum needed for backtest
CANDLE_LIMIT = 1000  # max per request (OKX supports up to 100)

# ---------------------------------------------------------------------------
# Backfill
# ---------------------------------------------------------------------------

async def backfill_okx(symbols: list[str]):
    """Fetch and store OKX candles for all symbols/timeframes. Paginates backwards to get full history."""
    import time as _time
    provider = OKXProvider()
    total = 0
    BATCH = 100  # OKX hard cap per request
    MAX_PAGES = 15  # up to ~1500 candles per symbol/tf

    # Timeframe to ms mapping
    TF_MS = {"4h": 4*3600*1000, "1d": 86400*1000}

    try:
        for sym_base in symbols:
            symbol = f"{sym_base}/USDT"
            for tf in TIMEFRAMES:
                print(f"  OKX {symbol} {tf}...", end=" ", flush=True)
                try:
                    all_candles = []
                    tf_ms = TF_MS.get(tf, 4*3600*1000)

                    # First batch: most recent 100
                    batch = await provider.get_ohlcv(symbol, timeframe=tf, limit=BATCH)
                    if not batch:
                        print("no data")
                        continue
                    all_candles.extend(batch)
                    oldest_ts = min(c.timestamp for c in batch)

                    # Paginate backwards: each iteration starts before the oldest candle we have
                    for _ in range(MAX_PAGES - 1):
                        since = oldest_ts - BATCH * tf_ms
                        batch = await provider.get_ohlcv(symbol, timeframe=tf, limit=BATCH, since=since)
                        if not batch:
                            break
                        all_candles.extend(batch)
                        oldest_ts = min(c.timestamp for c in batch)
                        if len(batch) < BATCH:
                            break
                        await asyncio.sleep(0.3)

                    # Deduplicate and sort
                    seen = set()
                    unique = []
                    for c in all_candles:
                        if c.timestamp not in seen:
                            seen.add(c.timestamp)
                            unique.append(c)
                    unique.sort(key=lambda c: c.timestamp)

                    async with Database.get_session() as session:
                        for c in unique:
                            await session.merge(DbCandle(
                                symbol=symbol,
                                provider="okx",
                                timeframe=tf,
                                timestamp=c.timestamp,
                                open=c.open,
                                high=c.high,
                                low=c.low,
                                close=c.close,
                                volume=c.volume,
                            ))
                        await session.commit()
                    print(f"{len(unique)} candles")
                    total += len(unique)
                except Exception as e:
                    print(f"error: {e}")

                await asyncio.sleep(0.5)
    finally:
        await provider.close()

    print(f"\nBackfill done: {total:,} candles stored (provider=okx)\n")
    return total


# ---------------------------------------------------------------------------
# Observations (reused from run_signal_backtest)
# ---------------------------------------------------------------------------

def print_observations(all_signals: list, cfg: BacktestConfig):
    print("\n" + "=" * 70)
    print("OKX BACKTEST OBSERVATIONS")
    print("=" * 70)

    if not all_signals:
        print("  No signals fired.")
        return

    stats = compute_stats(all_signals)

    tp_label = "adaptive" if cfg.tp_adaptive and cfg.tp_mult == 0 else f"{cfg.tp_mult}xATR"
    print(f"\n  OVERALL: {stats['total']} signals | "
          f"{stats['wins']}W {stats['losses']}L {stats['reviews']}R | "
          f"Win Rate: {stats['win_rate']}% (break-even = 33.3%)")
    print(f"  Total Profit: {stats['total_r']:+.1f}R | Avg RR: {stats['avg_rr']:.2f}:1")
    print(f"  Settings: SL={cfg.sl_mult}xATR | TP={tp_label} | MinConf={cfg.min_titan_confidence}% | Provider=okx")

    # Direction breakdown
    longs = [s for s in all_signals if s["direction"] == "LONG"]
    shorts = [s for s in all_signals if s["direction"] == "SHORT"]
    for label, subset in [("LONGS", longs), ("SHORTS", shorts)]:
        if not subset:
            continue
        w = sum(1 for s in subset if s["outcome"] == "WIN")
        l = sum(1 for s in subset if s["outcome"] == "LOSS")
        cl = w + l
        wr = round(w / cl * 100, 1) if cl > 0 else "N/A"
        print(f"  {label}: {len(subset)} signals, {wr}% WR")

    # Per-coin
    for symbol, coin_stats in sorted(stats["coin_results"].items()):
        sigs = [s for s in all_signals if s["symbol"] == symbol]
        longs_c = [s for s in sigs if s["direction"] == "LONG"]
        shorts_c = [s for s in sigs if s["direction"] == "SHORT"]
        print(f"\n  {symbol}:")
        print(f"    Total: {coin_stats['total']} ({len(longs_c)}L, {len(shorts_c)}S)")
        print(f"    W/L/R: {coin_stats['wins']}/{coin_stats['losses']}/{coin_stats['reviews']}")
        print(f"    WR: {coin_stats['win_rate']}% | P/L: {coin_stats['profit_r']:+.1f}R")

        by_state = defaultdict(list)
        for s in sigs:
            by_state[s["market_state"]].append(s)
        for state, state_sigs in sorted(by_state.items()):
            sw = sum(1 for s in state_sigs if s["outcome"] == "WIN")
            scl = sum(1 for s in state_sigs if s["outcome"] in ("WIN", "LOSS"))
            swr = round(sw / scl * 100, 1) if scl > 0 else "N/A"
            print(f"      {state:15s}: {len(state_sigs)} signals, {swr}% WR")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    print("=" * 70)
    print("OKX Backtest Pipeline")
    print(f"Coins: {', '.join(SYMBOLS)}")
    print("=" * 70)

    Database.init()
    await Database.create_tables()

    # Phase 1: Backfill
    if not SKIP_BACKFILL:
        print("\n--- Phase 1: OKX Backfill ---")
        await backfill_okx(SYMBOLS)
    else:
        print("\n--- Phase 1: Skipped (--skip-backfill) ---")

    # Phase 2: Backtest
    print("\n--- Phase 2: OKX Backtest ---")
    config = BacktestConfig(
        symbols=SYMBOLS,
        provider="okx",
        sl_mult=SL_MULT,
        min_titan_confidence=MIN_CONF,
        tp_adaptive=True,
        block_sleeping=True,
        block_volatile=True,
        macro_guard=True,
    )
    print(f"Config: {config.name} | Provider: okx")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'WRITE TO DB'}")

    data = await load_and_prepare_data(config.symbols, provider="okx")

    all_signals = []
    for coin in config.symbols:
        coin_data = data["coin_data"].get(coin, {})
        df_4h = coin_data.get("4h")
        df_1d = coin_data.get("1d")
        if df_4h is None or df_1d is None or df_4h.empty:
            print(f"  [{coin}] No OKX data — skipping")
            continue
        sigs = await backtest_symbol(
            f"{coin}/USDT", df_4h, df_1d,
            data["btc_4h"], data["btc_macro_biases"],
            config,
        )
        all_signals.extend(sigs)

    print_observations(all_signals, config)

    if not DRY_RUN and all_signals:
        from app.schemas.signal_log import SignalLog
        print(f"\nWriting {len(all_signals)} signals to signal_log (source=backtest-okx)...")
        async with Database.get_session() as session:
            for sig in all_signals:
                session.add(SignalLog(**sig))
            await session.commit()
        print("Done.")
    elif DRY_RUN:
        print("\nDry run — nothing written to DB.")

    await Database.close()


if __name__ == "__main__":
    asyncio.run(main())
