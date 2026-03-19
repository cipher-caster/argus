"""
BTC Titan Deep Dive — Extended Backtest + Parameter Sweep
==========================================================
Goes deeper on the winning strategy (Titan) with more data and
multiple parameter combinations.

Usage:
    docker compose exec backend python -m scripts.btc_titan_deep_dive
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
from itertools import product

import pandas as pd
import ccxt.async_support as ccxt

sys.path.insert(0, "/app")

from app.strategies.titan import TitanStrategy

titan = TitanStrategy()

SYMBOL = "BTC/USDT"

# Extended data: fetch maximum available candles
TIMEFRAME_FETCH = {
    "1h":  ("1h",  1000),   # ~41 days
    "4h":  ("4h",  1000),   # ~166 days
    "1d":  ("1d",  500),    # ~1.4 years
}


async def fetch_candles(exchange, symbol, timeframe, limit):
    print(f"  Fetching {symbol} {timeframe} (limit={limit})...")
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["ts_ms"] = df["timestamp"]
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df
    except Exception as e:
        print(f"  Error: {e}")
        return pd.DataFrame()


def titan_backtest_with_params(
    df: pd.DataFrame,
    sl_mult: float,
    tp_mult_fixed: float = 0,  # 0 = adaptive
    min_confidence: int = 55,
    warmup: int = 200,
) -> Dict[str, Any]:
    """
    Walk-forward Titan backtest with custom SL/TP parameters.
    """
    if df.empty or len(df) < warmup + 10:
        return {"error": "Insufficient data"}

    trades = []
    active_trade = None
    signals_count = 0

    for i in range(warmup, len(df)):
        row = df.iloc[i]
        price = float(row["close"])

        # Manage active trade
        if active_trade:
            high = row["high"]
            low = row["low"]
            result = None
            pnl = 0.0

            if active_trade["type"] == "LONG":
                if low <= active_trade["sl"]:
                    result = "LOSS"
                    pnl = (active_trade["sl"] - active_trade["entry"]) / active_trade["entry"]
                elif high >= active_trade["tp"]:
                    result = "WIN"
                    pnl = (active_trade["tp"] - active_trade["entry"]) / active_trade["entry"]
            elif active_trade["type"] == "SHORT":
                if high >= active_trade["sl"]:
                    result = "LOSS"
                    pnl = (active_trade["entry"] - active_trade["sl"]) / active_trade["entry"]
                elif low <= active_trade["tp"]:
                    result = "WIN"
                    pnl = (active_trade["entry"] - active_trade["tp"]) / active_trade["entry"]

            if result:
                active_trade["result"] = result
                active_trade["pnl"] = pnl
                trades.append(active_trade)
                active_trade = None
                continue

        # Check for signal
        if pd.isna(row.get("rsi")) or pd.isna(row.get("ema200")):
            continue

        ema = row.get("ema200")
        trend = "BULLISH" if not pd.isna(ema) and price > ema else "BEARISH"
        momentum = titan._analyze_momentum(row)
        volatility = titan._analyze_volatility(row)

        recent_window = df.iloc[max(0, i - 4):i + 1]
        bull_sweeps = recent_window[recent_window["sweep_type"] == "bullish"]
        bear_sweeps = recent_window[recent_window["sweep_type"] == "bearish"]
        recent_sweep = "bullish" if not bull_sweeps.empty else ("bearish" if not bear_sweeps.empty else None)

        t_result = titan._generate_signal(trend, momentum, volatility, row, recent_sweep)
        t_signal = t_result["type"]
        t_confidence = t_result["confidence"]

        is_long = t_signal in ("BUY", "BUY_LIMIT")
        is_short = t_signal in ("SELL", "SELL_LIMIT")

        if not (is_long or is_short) or t_confidence < min_confidence:
            continue

        signals_count += 1
        direction = "LONG" if is_long else "SHORT"

        if active_trade and active_trade["type"] == ("LONG" if is_long else "SHORT"):
            continue

        atr = float(row.get("atr", 0))
        if atr <= 0:
            continue

        # TP logic
        if tp_mult_fixed > 0:
            tp_mult = tp_mult_fixed
        else:
            adx = row.get("adx", 25)
            tp_mult = 3.0 if (not pd.isna(adx) and adx > 40) else 2.0

        if is_long:
            sl = price - (atr * sl_mult)
            tp = price + (atr * tp_mult)
        else:
            sl = price + (atr * sl_mult)
            tp = price - (atr * tp_mult)

        active_trade = {
            "type": "LONG" if is_long else "SHORT",
            "entry": price,
            "tp": tp,
            "sl": sl,
        }

    # Stats
    total = len(trades)
    wins = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    win_rate = (wins / total * 100) if total > 0 else 0

    total_r = 0.0
    for t in trades:
        risk = abs(t["entry"] - t["sl"])
        reward = abs(t["tp"] - t["entry"])
        rr = reward / risk if risk > 0 else 0
        if t["result"] == "WIN":
            total_r += rr
        else:
            total_r -= 1.0

    ev = total_r / (wins + losses) if (wins + losses) > 0 else 0

    # Max drawdown
    equity = [0.0]
    for t in trades:
        risk = abs(t["entry"] - t["sl"])
        reward = abs(t["tp"] - t["entry"])
        rr = reward / risk if risk > 0 else 0
        equity.append(equity[-1] + rr if t["result"] == "WIN" else equity[-1] - 1.0)

    peak = 0
    max_dd = 0
    for e in equity:
        peak = max(peak, e)
        max_dd = max(max_dd, peak - e)

    # Longs vs shorts
    longs = [t for t in trades if t["type"] == "LONG"]
    shorts = [t for t in trades if t["type"] == "SHORT"]
    long_wr = round(sum(1 for t in longs if t["result"] == "WIN") / len(longs) * 100, 1) if longs else None
    short_wr = round(sum(1 for t in shorts if t["result"] == "WIN") / len(shorts) * 100, 1) if shorts else None

    return {
        "signals": signals_count,
        "trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "total_r": round(total_r, 2),
        "ev": round(ev, 3),
        "max_dd": round(max_dd, 2),
        "profit_factor": round(wins / max(losses, 1), 2),
        "longs": len(longs),
        "long_wr": long_wr,
        "shorts": len(shorts),
        "short_wr": short_wr,
    }


def time_years(df):
    if len(df) < 2:
        return 1.0
    return (df.iloc[-1]["ts_ms"] - df.iloc[0]["ts_ms"]) / (365.25 * 24 * 3600 * 1000)


async def run():
    print("=" * 70)
    print("BTC TITAN DEEP DIVE — Extended Backtest + Parameter Sweep")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)

    exchange = ccxt.binance({"enableRateLimit": True})
    try:
        data = {}
        for label, (tf, limit) in TIMEFRAME_FETCH.items():
            data[label] = await fetch_candles(exchange, SYMBOL, tf, limit)
    finally:
        await exchange.close()

    # ============================================================
    # Part 1: Extended base backtest
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 PART 1: Extended Base Backtest (default params)")
    print("=" * 70)

    for tf, df in data.items():
        years = time_years(df)
        print(f"\n--- {tf}: {len(df)} candles ({years:.2f}yr) ---")
        if df.empty:
            continue
        titan._add_indicators(df)
        r = titan_backtest_with_params(df, sl_mult=1.5)
        if "error" in r:
            print(f"  Error: {r['error']}")
            continue
        ann = r["total_r"] / years if years > 0 else 0
        print(f"  Trades: {r['trades']} | WR: {r['win_rate']}%")
        print(f"  Total R: {r['total_r']:+.2f} | EV: {r['ev']:+.3f}R")
        print(f"  Ann.R: {ann:+.2f}R/yr | MaxDD: {r['max_dd']}R | PF: {r['profit_factor']}")
        print(f"  Longs: {r['longs']} (WR={r['long_wr']}%) | Shorts: {r['shorts']} (WR={r['short_wr']}%)")

    # ============================================================
    # Part 2: Parameter sweep on 1h and 1d (best performers)
    # ============================================================
    print("\n" + "=" * 70)
    print("🔬 PART 2: Parameter Sweep — Titan on 1h and 1d")
    print("=" * 70)

    sl_mults = [1.0, 1.25, 1.5, 2.0, 2.5]
    tp_mults = [0, 1.5, 2.0, 2.5, 3.0, 4.0]  # 0 = adaptive
    min_confs = [50, 55, 60, 70]

    sweep_results = []

    for tf_label in ["1h", "1d"]:
        df = data.get(tf_label, pd.DataFrame())
        if df.empty:
            continue
        years = time_years(df)
        print(f"\n--- Sweeping {tf_label} ({len(df)} candles, {years:.2f}yr) ---")

        for sl, tp, mc in product(sl_mults, tp_mults, min_confs):
            r = titan_backtest_with_params(df, sl_mult=sl, tp_mult_fixed=tp, min_confidence=mc)
            if "error" in r or r["trades"] < 3:
                continue

            ann = r["total_r"] / years if years > 0 else 0

            result = {
                "tf": tf_label,
                "sl": sl,
                "tp": tp if tp > 0 else "adaptive",
                "min_conf": mc,
                **r,
                "ann_r": round(ann, 2),
            }
            sweep_results.append(result)

    # ============================================================
    # Part 3: Rank sweep results
    # ============================================================
    print("\n" + "=" * 70)
    print("🏆 TOP 20 CONFIGURATIONS (by EV/Trade)")
    print("=" * 70)

    sweep_results.sort(key=lambda x: x["ev"], reverse=True)
    top20 = sweep_results[:20]

    print(f"\n{'Rank':>4} {'TF':>3} {'SL':>5} {'TP':>8} {'Conf':>4} {'Trades':>6} {'WR':>5} "
          f"{'EV':>7} {'TotalR':>8} {'MaxDD':>6} {'PF':>5} {'Ann.R':>8}")
    print("-" * 85)

    for i, r in enumerate(top20):
        tp_str = str(r["tp"])
        print(f"{i+1:>4} {r['tf']:>3} {r['sl']:>5.2f} {tp_str:>8} {r['min_conf']:>4} "
              f"{r['trades']:>6} {r['win_rate']:>5}% {r['ev']:>+7.3f} {r['total_r']:>+8.2f} "
              f"{r['max_dd']:>6.1f} {r['profit_factor']:>5.2f} {r['ann_r']:>+8.2f}")

    # ============================================================
    # Part 4: Best per timeframe
    # ============================================================
    print("\n" + "=" * 70)
    print("🎯 BEST CONFIG PER TIMEFRAME")
    print("=" * 70)

    for tf in ["1h", "1d"]:
        tf_results = [r for r in sweep_results if r["tf"] == tf]
        if not tf_results:
            continue
        best = max(tf_results, key=lambda x: x["ev"])
        best_tp = best["tp"]
        tp_str = "adaptive" if best_tp == "adaptive" else f"{best_tp}xATR"
        print(f"\n  {tf}: SL={best['sl']}xATR, TP={tp_str}, MinConf={best['min_conf']}")
        print(f"    Trades={best['trades']} | WR={best['win_rate']}% | EV={best['ev']:+.3f}R")
        print(f"    Total R={best['total_r']:+.2f} | Ann.R={best['ann_r']:+.2f}R/yr")
        print(f"    MaxDD={best['max_dd']}R | PF={best['profit_factor']}")
        print(f"    Longs={best['longs']} (WR={best['long_wr']}%) | Shorts={best['shorts']} (WR={best['short_wr']}%)")

    # ============================================================
    # Part 5: Risk/Reward analysis
    # ============================================================
    print("\n" + "=" * 70)
    print("📈 RISK/REWARD SENSITIVITY (1d timeframe)")
    print("=" * 70)

    df_1d = data.get("1d", pd.DataFrame())
    if not df_1d.empty:
        print(f"\n{'SL Mult':>8} {'TP Mult':>8} {'R:R':>5} {'Trades':>6} {'WR':>5} {'EV':>7} {'TotalR':>8}")
        print("-" * 55)
        for sl in [1.0, 1.25, 1.5, 2.0]:
            for tp in [1.5, 2.0, 2.5, 3.0, 4.0]:
                r = titan_backtest_with_params(df_1d, sl_mult=sl, tp_mult_fixed=tp, min_confidence=55)
                if r.get("trades", 0) < 3:
                    continue
                rr = round(tp / sl, 2)
                print(f"{sl:>8.2f} {tp:>8.1f} {rr:>5.2f} {r['trades']:>6} {r['win_rate']:>5}% "
                      f"{r['ev']:>+7.3f} {r['total_r']:>+8.2f}")

    # Save
    output = {
        "top20": top20,
        "all_sweep": sweep_results,
    }
    path = "/tmp/btc_titan_sweep.json"
    with open(path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n📁 Full sweep results: {path}")


if __name__ == "__main__":
    asyncio.run(run())
