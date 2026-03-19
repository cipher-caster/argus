#!/usr/bin/env python3
"""
Trading Optimization Sweep Script
====================================
Runs parameter sweeps over BacktestConfig knobs, saves every result as an
OptimizationExperiment row, prints a ranked table, and optionally applies
the best config to Redis.

Usage (inside Docker):
    docker compose exec -T backend python scripts/optimize_trading.py --preset=sl_sweep
    docker compose exec -T backend python scripts/optimize_trading.py --preset=tp_sweep
    docker compose exec -T backend python scripts/optimize_trading.py --preset=confidence_sweep
    docker compose exec -T backend python scripts/optimize_trading.py --preset=gate_sweep
    docker compose exec -T backend python scripts/optimize_trading.py --preset=full_grid
    docker compose exec -T backend python scripts/optimize_trading.py --show-best
    docker compose exec -T backend python scripts/optimize_trading.py --apply-best
    docker compose exec -T backend python scripts/optimize_trading.py --custom='{"sl_mult":2.0,"tp_mult":2.5}'

Sweep presets:
    sl_sweep        SL = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5] × ATR — 6 configs
    tp_sweep        TP = [adaptive, 1.5, 2.0, 2.5, 3.0, 3.5] × ATR — 6 configs
    confidence_sweep  min_titan_conf = [50, 55, 60, 65, 70, 75] — 6 configs
    gate_sweep      {block_sleeping, macro_guard, strict_macro} permutations — 8 configs
    full_grid       top-3 SL × top-3 TP × top-2 confidence — up to 18 configs
"""

import asyncio
import json
import sys
import os
import time
import uuid
from datetime import timezone, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import select
from sqlalchemy import desc

from app.storage import Database, RedisClient
from app.schemas.optimization import OptimizationExperiment
from app.trading.backtest_engine import (
    BacktestConfig,
    DEFAULT_COINS,
    load_and_prepare_data,
    backtest_symbol,
    compute_stats,
)

# ---------------------------------------------------------------------------
# Sweep presets
# ---------------------------------------------------------------------------

BASE_SYMBOLS = list(DEFAULT_COINS)

def sl_sweep_configs() -> list[BacktestConfig]:
    return [
        BacktestConfig(symbols=BASE_SYMBOLS, sl_mult=v, tp_adaptive=True,
                       block_sleeping=True, macro_guard=True)
        for v in [1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
    ]

def tp_sweep_configs() -> list[BacktestConfig]:
    configs = [
        BacktestConfig(symbols=BASE_SYMBOLS, sl_mult=1.5, tp_mult=0.0,
                       tp_adaptive=True, block_sleeping=True, macro_guard=True),
    ]
    for v in [1.5, 2.0, 2.5, 3.0, 3.5]:
        configs.append(BacktestConfig(symbols=BASE_SYMBOLS, sl_mult=1.5, tp_mult=v,
                                       tp_adaptive=False, block_sleeping=True, macro_guard=True))
    return configs

def confidence_sweep_configs() -> list[BacktestConfig]:
    return [
        BacktestConfig(symbols=BASE_SYMBOLS, sl_mult=1.5, tp_adaptive=True,
                       min_titan_confidence=v, block_sleeping=True, macro_guard=True)
        for v in [50, 55, 60, 65, 70, 75]
    ]

def gate_sweep_configs() -> list[BacktestConfig]:
    configs = []
    for block_sleep in [False, True]:
        for macro in [False, True]:
            for strict in [False, True]:
                if strict and not macro:
                    continue  # strict implies macro; skip invalid combo
                configs.append(BacktestConfig(
                    symbols=BASE_SYMBOLS, sl_mult=1.5, tp_adaptive=True,
                    block_sleeping=block_sleep, macro_guard=macro, strict_macro=strict,
                ))
    return configs

def full_grid_configs() -> list[BacktestConfig]:
    """top-3 SL × top-3 TP × top-2 confidence = 18 configs"""
    configs = []
    for sl in [1.25, 1.5, 1.75]:
        for tp, adaptive in [(0.0, True), (2.0, False), (2.5, False)]:
            for conf in [55, 65]:
                configs.append(BacktestConfig(
                    symbols=BASE_SYMBOLS, sl_mult=sl,
                    tp_mult=tp, tp_adaptive=adaptive,
                    min_titan_confidence=conf,
                    block_sleeping=True, macro_guard=True,
                ))
    return configs

PRESETS = {
    "sl_sweep": sl_sweep_configs,
    "tp_sweep": tp_sweep_configs,
    "confidence_sweep": confidence_sweep_configs,
    "gate_sweep": gate_sweep_configs,
    "full_grid": full_grid_configs,
}

# ---------------------------------------------------------------------------
# Run a single config
# ---------------------------------------------------------------------------

async def run_config(cfg: BacktestConfig, data: dict) -> dict:
    """Run backtest for one config across all coins. Returns stats dict."""
    all_signals = []
    for coin in cfg.symbols:
        coin_data = data["coin_data"].get(coin, {})
        df_4h = coin_data.get("4h")
        df_1d = coin_data.get("1d")
        if df_4h is None or df_1d is None:
            continue
        sigs = await backtest_symbol(
            f"{coin}/USDT", df_4h, df_1d,
            data["btc_4h"], data["btc_macro_biases"],
            cfg,
        )
        all_signals.extend(sigs)
    return compute_stats(all_signals)


async def save_experiment(
    cfg: BacktestConfig,
    stats: dict,
    run_id: str,
    min_conviction: int = 65,
    notes: str = None,
) -> OptimizationExperiment:
    exp = OptimizationExperiment(
        run_id=run_id,
        name=cfg.name,
        created_at=int(time.time() * 1000),
        symbols=",".join(cfg.symbols),
        sl_mult=cfg.sl_mult,
        tp_mult=cfg.tp_mult,
        tp_adaptive=cfg.tp_adaptive,
        min_titan_confidence=cfg.min_titan_confidence,
        block_sleeping=cfg.block_sleeping,
        block_volatile=cfg.block_volatile,
        macro_guard=cfg.macro_guard,
        strict_macro=cfg.strict_macro,
        min_conviction=min_conviction,
        total_signals=stats["total"],
        wins=stats["wins"],
        losses=stats["losses"],
        reviews=stats["reviews"],
        win_rate=stats["win_rate"],
        total_r=stats["total_r"],
        ev_per_trade=stats["ev_per_trade"],
        avg_rr=stats["avg_rr"],
        coin_results=json.dumps(stats["coin_results"]),
        notes=notes,
    )
    async with Database.get_session() as session:
        session.add(exp)
        await session.commit()
        await session.refresh(exp)
    return exp


# ---------------------------------------------------------------------------
# Print results table
# ---------------------------------------------------------------------------

def print_results_table(experiments: list[OptimizationExperiment]):
    print("\n" + "=" * 90)
    print(f"{'#':<4} {'Name':<40} {'Signals':<8} {'WR%':<7} {'TotalR':<8} {'EV/trade':<10} {'Prod'}")
    print("-" * 90)
    for i, e in enumerate(experiments, 1):
        wr = f"{e.win_rate:.1f}%" if e.win_rate is not None else "N/A"
        ev = f"{e.ev_per_trade:+.3f}R" if e.ev_per_trade is not None else "N/A"
        prod = "★" if e.is_production else ""
        print(f"{i:<4} {e.name:<40} {e.total_signals:<8} {wr:<7} {e.total_r:+.1f}R{'':<4} {ev:<10} {prod}")
    print("=" * 90)


# ---------------------------------------------------------------------------
# Apply best config to Redis
# ---------------------------------------------------------------------------

async def apply_config_to_redis(exp: OptimizationExperiment):
    r = RedisClient.get_instance()

    # Update signal_log:config
    sl_cfg_raw = await r.get("signal_log:config")
    sl_cfg = json.loads(sl_cfg_raw) if sl_cfg_raw else {}
    sl_cfg["min_titan_confidence"] = exp.min_titan_confidence
    sl_cfg["block_sleeping"] = exp.block_sleeping
    sl_cfg["block_volatile"] = exp.block_volatile
    sl_cfg["macro_guard"] = exp.macro_guard
    await r.set("signal_log:config", json.dumps(sl_cfg))

    # Update trading:config
    t_cfg_raw = await r.get("trading:config")
    t_cfg = json.loads(t_cfg_raw) if t_cfg_raw else {}
    t_cfg["min_conviction"] = exp.min_conviction
    await r.set("trading:config", json.dumps(t_cfg))

    # Mark as production in DB
    async with Database.get_session() as session:
        # Unmark previous production
        prev = await session.execute(
            select(OptimizationExperiment).where(OptimizationExperiment.is_production == True)
        )
        for p in prev.scalars().all():
            p.is_production = False
            session.add(p)
        exp.is_production = True
        session.add(exp)
        await session.commit()

    print(f"\n  Applied config '{exp.name}' to Redis.")
    print(f"  signal_log:config updated: min_titan_confidence={exp.min_titan_confidence}, "
          f"block_sleeping={exp.block_sleeping}, macro_guard={exp.macro_guard}")
    print(f"  trading:config updated: min_conviction={exp.min_conviction}")


# ---------------------------------------------------------------------------
# --show-best
# ---------------------------------------------------------------------------

async def show_best(min_signals: int = 30):
    async with Database.get_session() as session:
        result = await session.execute(
            select(OptimizationExperiment)
            .where(OptimizationExperiment.total_signals >= min_signals)
            .order_by(desc(OptimizationExperiment.ev_per_trade))
            .limit(20)
        )
        experiments = result.scalars().all()

    if not experiments:
        print(f"No experiments with >= {min_signals} signals found.")
        return

    print(f"\nTop {len(experiments)} configs by EV/trade (min {min_signals} signals):")
    print_results_table(experiments)

    best = experiments[0]
    print(f"\nBest: '{best.name}' — EV/trade={best.ev_per_trade:+.3f}R, "
          f"WR={best.win_rate}%, Total={best.total_r:+.1f}R")
    return best


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    args = sys.argv[1:]

    Database.init()
    await Database.create_tables()

    # --show-best
    if "--show-best" in args:
        await show_best()
        await Database.close()
        return

    # --apply-best
    if "--apply-best" in args:
        best = await show_best()
        if best:
            await apply_config_to_redis(best)
        await Database.close()
        return

    # --custom='{"sl_mult":2.0,...}'
    custom_arg = next((a for a in args if a.startswith("--custom=")), None)
    if custom_arg:
        params = json.loads(custom_arg.split("=", 1)[1])
        configs = [BacktestConfig(symbols=BASE_SYMBOLS, **params)]
        preset_name = "custom"
    else:
        # --preset=X
        preset_arg = next((a for a in args if a.startswith("--preset=")), None)
        if not preset_arg:
            print("Usage: optimize_trading.py --preset=sl_sweep|tp_sweep|confidence_sweep|gate_sweep|full_grid")
            print("       optimize_trading.py --show-best")
            print("       optimize_trading.py --apply-best")
            print("       optimize_trading.py --custom='{...}'")
            sys.exit(1)
        preset_name = preset_arg.split("=")[1]
        if preset_name not in PRESETS:
            print(f"Unknown preset '{preset_name}'. Choose from: {', '.join(PRESETS)}")
            sys.exit(1)
        configs = PRESETS[preset_name]()

    run_id = str(uuid.uuid4())
    print(f"\nArgus Trading Optimizer — preset={preset_name}, run_id={run_id}")
    print(f"Configs to test: {len(configs)}")
    print(f"Symbols: {', '.join(BASE_SYMBOLS)}\n")

    print("Loading candle data (shared across all configs)...")
    data = await load_and_prepare_data(BASE_SYMBOLS)
    print(f"  Data loaded.\n")

    experiments = []
    for i, cfg in enumerate(configs, 1):
        print(f"[{i}/{len(configs)}] {cfg.name}")
        t0 = time.time()
        stats = await run_config(cfg, data)
        elapsed = time.time() - t0
        exp = await save_experiment(cfg, stats, run_id)
        experiments.append(exp)
        wr = f"{stats['win_rate']:.1f}%" if stats["win_rate"] else "N/A"
        ev = f"{stats['ev_per_trade']:+.3f}R" if stats["ev_per_trade"] else "N/A"
        print(f"  → {stats['total']} signals | WR={wr} | Total={stats['total_r']:+.1f}R | EV={ev} ({elapsed:.0f}s)")

    # Sort by EV/trade (best first)
    experiments.sort(key=lambda e: (e.ev_per_trade or -999), reverse=True)

    print("\nResults ranked by EV/trade:")
    print_results_table(experiments)

    best = experiments[0]
    print(f"\nBest config: '{best.name}'")
    print(f"  EV/trade: {best.ev_per_trade:+.3f}R | WR: {best.win_rate}% | Total: {best.total_r:+.1f}R")
    print(f"\nTo apply: docker compose exec -T backend python scripts/optimize_trading.py --apply-best")

    await RedisClient.close()
    await Database.close()


if __name__ == "__main__":
    asyncio.run(main())
