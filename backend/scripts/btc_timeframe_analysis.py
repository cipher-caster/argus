"""
BTC Multi-Timeframe Profitability Analysis
===========================================
Runs Oracle + Titan strategies on BTC across multiple timeframes to find
the most profitable configuration.

Micro timeframes tested: 15m, 1h, 4h, 1d
Each paired with appropriate macro trend timeframe.

Usage (inside Docker):
    docker compose exec backend python -m scripts.btc_timeframe_analysis
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import ccxt.async_support as ccxt

sys.path.insert(0, "/app")

from app.strategies.oracle import OracleStrategy
from app.strategies.titan import TitanStrategy

oracle = OracleStrategy()
titan = TitanStrategy()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SYMBOL = "BTC/USDT"

# (micro_tf, macro_tf, label, candle_limit)
# Macro is ~4x the micro for trend context
TIMEFRAME_CONFIGS = [
    ("15m", "4h",  "15m / 4h",  1000),
    ("1h",  "1d",  "1h / 1d",    500),
    ("4h",  "1w",  "4h / 1w",    300),
    ("1d",  "1M",  "1d / 1M",    300),
]

# Titan single-timeframe configs
TITAN_TIMEFRAMES = [
    ("15m", 1000),
    ("1h",  500),
    ("4h",  300),
    ("1d",  300),
]

WARMUP = 200  # candles to skip at start for indicator warm-up


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

async def fetch_candles(exchange, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Fetch OHLCV candles from Binance via CCXT."""
    print(f"  Fetching {symbol} {timeframe} (limit={limit})...")
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv:
            return pd.DataFrame()
        
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["ts_ms"] = df["timestamp"]
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df
    except Exception as e:
        print(f"  Error fetching {symbol} {timeframe}: {e}")
        return pd.DataFrame()


async def fetch_all_data() -> dict:
    """Fetch all required BTC data across timeframes."""
    exchange = ccxt.binance({"enableRateLimit": True})
    
    try:
        all_data = {}
        
        # Fetch Oracle micro/macro combos
        for micro_tf, macro_tf, label, limit in TIMEFRAME_CONFIGS:
            print(f"\n--- Oracle Config: {label} ---")
            micro_df, macro_df = await asyncio.gather(
                fetch_candles(exchange, SYMBOL, micro_tf, limit),
                fetch_candles(exchange, SYMBOL, macro_tf, limit),
            )
            all_data[f"oracle_{micro_tf}"] = {
                "micro": micro_df,
                "macro": macro_df,
                "label": label,
                "micro_tf": micro_tf,
                "macro_tf": macro_tf,
            }
        
        # Fetch Titan timeframes
        for tf, limit in TITAN_TIMEFRAMES:
            print(f"\n--- Titan Config: {tf} ---")
            df = await fetch_candles(exchange, SYMBOL, tf, limit)
            all_data[f"titan_{tf}"] = {
                "df": df,
                "timeframe": tf,
            }
        
        return all_data
    finally:
        await exchange.close()


# ---------------------------------------------------------------------------
# Oracle backtest (adapted from oracle.py _run_backtest)
# ---------------------------------------------------------------------------

def oracle_backtest(df_micro: pd.DataFrame, df_macro: pd.DataFrame) -> Dict[str, Any]:
    """
    Walk-forward Oracle backtest on micro timeframe with macro context.
    Returns signals, trades, and performance stats.
    """
    if df_micro.empty or df_macro.empty:
        return {"error": "Empty data", "signals": [], "stats": {}}

    signals = []
    trades = []
    active_trade = None

    # Pre-calculate macro biases
    macro_biases = {}
    for _, row in df_macro.iterrows():
        macro_biases[row["timestamp"]] = oracle._calculate_macro_bias(row)

    for i in range(WARMUP, len(df_micro)):
        row = df_micro.iloc[i]

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
                active_trade["exit_time"] = row["ts_ms"]
                trades.append(active_trade)
                active_trade = None
                continue

        # Check for new entry
        if pd.isna(row.get("rsi")) or pd.isna(row.get("ema200")):
            continue

        # Find matching macro bias
        ts = row["timestamp"]
        macro_ts = [t for t in macro_biases.keys() if t <= ts]
        if not macro_ts:
            continue
        m_bias = macro_biases[max(macro_ts)]

        e_score = oracle._calculate_earnest_score(row)["score"]
        sig = oracle._synthesize_signal(e_score, m_bias["score"])

        if sig in ["STRONG_BUY", "BUY", "STRONG_SELL", "SELL"]:
            signals.append({
                "timestamp": row["ts_ms"],
                "signal": sig,
                "price": float(row["close"]),
            })

            atr = float(row["atr"]) if not pd.isna(row.get("atr")) else float(row["close"]) * 0.01
            price = float(row["close"])

            if "BUY" in sig:
                active_trade = {
                    "type": "LONG",
                    "entry": price,
                    "tp": price + (atr * 3.0),
                    "sl": price - (atr * 1.5),
                    "start_time": row["ts_ms"],
                    "signal": sig,
                }
            elif "SELL" in sig:
                active_trade = {
                    "type": "SHORT",
                    "entry": price,
                    "tp": price - (atr * 3.0),
                    "sl": price + (atr * 1.5),
                    "start_time": row["ts_ms"],
                    "signal": sig,
                }

    # Stats
    total = len(trades)
    wins = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    win_rate = (wins / total * 100) if total > 0 else 0
    total_pnl = sum(t["pnl"] for t in trades) * 100

    # R-multiple stats
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

    # Per-signal-type breakdown
    by_signal = {}
    for t in trades:
        sig = t.get("signal", "UNKNOWN")
        if sig not in by_signal:
            by_signal[sig] = {"total": 0, "wins": 0, "total_r": 0.0}
        by_signal[sig]["total"] += 1
        if t["result"] == "WIN":
            by_signal[sig]["wins"] += 1
        risk = abs(t["entry"] - t["sl"])
        reward = abs(t["tp"] - t["entry"])
        rr = reward / risk if risk > 0 else 0
        if t["result"] == "WIN":
            by_signal[sig]["total_r"] += rr
        else:
            by_signal[sig]["total_r"] -= 1.0

    return {
        "signals": signals,
        "trades": trades,
        "stats": {
            "total_signals": len(signals),
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 1),
            "total_pnl_pct": round(total_pnl, 2),
            "total_r": round(total_r, 2),
            "ev_per_trade": round(ev, 3),
            "by_signal": by_signal,
        },
    }


# ---------------------------------------------------------------------------
# Titan backtest
# ---------------------------------------------------------------------------

def titan_backtest(df: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
    """
    Walk-forward Titan backtest on a single timeframe.
    """
    if df.empty or len(df) < WARMUP + 10:
        return {"error": "Insufficient data", "signals": [], "stats": {}}

    signals = []
    trades = []
    active_trade = None

    for i in range(WARMUP, len(df)):
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
                active_trade["exit_time"] = row["ts_ms"]
                trades.append(active_trade)
                active_trade = None
                continue

        # Check for signal
        if pd.isna(row.get("rsi")) or pd.isna(row.get("ema200")):
            continue

        ema = row.get("ema200")
        trend = "BULLISH" if not pd.isna(ema) and price > ema else "BEARISH"
        momentum = titan._analyze_momentum(row)
        volatility = titan._analyze_volatility(df.iloc[max(0, i - titan.squeeze_lookback + 1) : i + 1])

        # Check for recent sweeps
        recent_window = df.iloc[max(0, i - 4):i + 1]
        bull_sweeps = recent_window[recent_window["sweep_type"] == "bullish"]
        bear_sweeps = recent_window[recent_window["sweep_type"] == "bearish"]
        recent_sweep = "bullish" if not bull_sweeps.empty else ("bearish" if not bear_sweeps.empty else None)

        t_result = titan._generate_signal(trend, momentum, volatility, row, recent_sweep)
        t_signal = t_result["type"]
        t_confidence = t_result["confidence"]

        is_long = t_signal in ("BUY", "BUY_LIMIT")
        is_short = t_signal in ("SELL", "SELL_LIMIT")

        if not (is_long or is_short) or t_confidence < 55:
            continue

        direction = "LONG" if is_long else "SHORT"

        # Avoid duplicate same-direction signals
        if active_trade and active_trade["type"] == ("LONG" if is_long else "SHORT"):
            continue

        atr = float(row.get("atr", 0))
        if atr <= 0:
            continue

        # Adaptive TP based on trend strength
        adx = row.get("adx", 25)
        tp_mult = 3.0 if (not pd.isna(adx) and adx > 40) else 2.0

        if is_long:
            sl = price - (atr * 1.5)
            tp = price + (atr * tp_mult)
        else:
            sl = price + (atr * 1.5)
            tp = price - (atr * tp_mult)

        signals.append({
            "timestamp": row["ts_ms"],
            "signal": t_signal,
            "price": price,
            "confidence": t_confidence,
        })

        active_trade = {
            "type": "LONG" if is_long else "SHORT",
            "entry": price,
            "tp": tp,
            "sl": sl,
            "start_time": row["ts_ms"],
            "signal": t_signal,
            "confidence": t_confidence,
        }

    # Stats
    total = len(trades)
    wins = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    win_rate = (wins / total * 100) if total > 0 else 0
    total_pnl = sum(t["pnl"] for t in trades) * 100

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

    # By signal type
    by_signal = {}
    for t in trades:
        sig = t.get("signal", "UNKNOWN")
        if sig not in by_signal:
            by_signal[sig] = {"total": 0, "wins": 0, "total_r": 0.0}
        by_signal[sig]["total"] += 1
        if t["result"] == "WIN":
            by_signal[sig]["wins"] += 1
        risk = abs(t["entry"] - t["sl"])
        reward = abs(t["tp"] - t["entry"])
        rr = reward / risk if risk > 0 else 0
        if t["result"] == "WIN":
            by_signal[sig]["total_r"] += rr
        else:
            by_signal[sig]["total_r"] -= 1.0

    # Longs vs shorts
    long_trades = [t for t in trades if t["type"] == "LONG"]
    short_trades = [t for t in trades if t["type"] == "SHORT"]
    long_wins = sum(1 for t in long_trades if t["result"] == "WIN")
    short_wins = sum(1 for t in short_trades if t["result"] == "WIN")

    return {
        "signals": signals,
        "trades": trades,
        "stats": {
            "timeframe": timeframe,
            "total_signals": len(signals),
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 1),
            "total_pnl_pct": round(total_pnl, 2),
            "total_r": round(total_r, 2),
            "ev_per_trade": round(ev, 3),
            "longs": len(long_trades),
            "long_wins": long_wins,
            "shorts": len(short_trades),
            "short_wins": short_wins,
            "by_signal": by_signal,
        },
    }


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def compute_trade_metrics(trades: list) -> dict:
    """Compute advanced trade metrics: max drawdown, consecutive streaks, avg hold."""
    if not trades:
        return {}

    # Equity curve
    equity = [0.0]
    for t in trades:
        risk = abs(t["entry"] - t["sl"])
        reward = abs(t["tp"] - t["entry"])
        rr = reward / risk if risk > 0 else 0
        if t["result"] == "WIN":
            equity.append(equity[-1] + rr)
        else:
            equity.append(equity[-1] - 1.0)

    # Max drawdown (in R)
    peak = equity[0]
    max_dd = 0.0
    for e in equity:
        peak = max(peak, e)
        dd = peak - e
        max_dd = max(max_dd, dd)

    # Consecutive streaks
    max_win_streak = max_loss_streak = cur_win = cur_loss = 0
    for t in trades:
        if t["result"] == "WIN":
            cur_win += 1
            cur_loss = 0
            max_win_streak = max(max_win_streak, cur_win)
        else:
            cur_loss += 1
            cur_win = 0
            max_loss_streak = max(max_loss_streak, cur_loss)

    # Avg hold time (in hours)
    hold_hours = []
    for t in trades:
        if "start_time" in t and "exit_time" in t and t["exit_time"]:
            hours = (t["exit_time"] - t["start_time"]) / (1000 * 3600)
            if hours > 0:
                hold_hours.append(hours)

    return {
        "equity_curve_final_r": round(equity[-1], 2),
        "max_drawdown_r": round(max_dd, 2),
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "avg_hold_hours": round(sum(hold_hours) / len(hold_hours), 1) if hold_hours else None,
        "profit_factor": round(
            sum(1 for t in trades if t["result"] == "WIN") /
            max(sum(1 for t in trades if t["result"] == "LOSS"), 1),
            2
        ),
    }


def time_in_year_fraction(df: pd.DataFrame) -> float:
    """Return fraction of a year covered by the data."""
    if len(df) < 2:
        return 1.0
    start = df.iloc[0]["ts_ms"]
    end = df.iloc[-1]["ts_ms"]
    ms_per_year = 365.25 * 24 * 3600 * 1000
    return (end - start) / ms_per_year


def annualized_return(total_r: float, years: float) -> float:
    """Approximate annualized return from total R over N years."""
    if years <= 0:
        return 0.0
    return total_r / years


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

async def run_analysis():
    print("=" * 70)
    print("BTC MULTI-TIMEFRAME PROFITABILITY ANALYSIS")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)

    # Fetch data
    print("\n📡 Fetching BTC data from Binance...\n")
    all_data = await fetch_all_data()

    results = {"oracle": [], "titan": []}

    # -----------------------------------------------------------------------
    # Oracle analysis
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("🔮 ORACLE STRATEGY — Multi-Timeframe Analysis")
    print("=" * 70)

    for micro_tf, macro_tf, label, limit in TIMEFRAME_CONFIGS:
        key = f"oracle_{micro_tf}"
        data = all_data.get(key, {})
        micro_df = data.get("micro", pd.DataFrame())
        macro_df = data.get("macro", pd.DataFrame())

        print(f"\n--- {label} ---")
        print(f"  Micro: {len(micro_df)} candles | Macro: {len(macro_df)} candles")

        if micro_df.empty or macro_df.empty:
            print("  ⚠ Insufficient data, skipping")
            continue

        # Add indicators
        oracle._add_indicators(micro_df)
        oracle._add_indicators(macro_df)

        # Run backtest
        bt = oracle_backtest(micro_df, macro_df)
        stats = bt["stats"]
        trades = bt.get("trades", [])

        if "error" in bt:
            print(f"  ⚠ Error: {bt['error']}")
            continue

        # Advanced metrics
        metrics = compute_trade_metrics(trades)
        years = time_in_year_fraction(micro_df)
        ann_r = annualized_return(stats["total_r"], years)

        result = {
            "config": label,
            "micro_tf": micro_tf,
            "macro_tf": macro_tf,
            "data_range_years": round(years, 2),
            **stats,
            **metrics,
            "annualized_r": round(ann_r, 2),
        }
        results["oracle"].append(result)

        # Print
        print(f"  Signals: {stats['total_signals']} | Trades: {stats['total_trades']}")
        print(f"  Win Rate: {stats['win_rate']}%")
        print(f"  Total R: {stats['total_r']:+.2f}R | EV/Trade: {stats['ev_per_trade']:.3f}R")
        print(f"  PnL%: {stats['total_pnl_pct']:+.2f}%")
        print(f"  Annualized R: {ann_r:+.2f}R/yr (data: {years:.1f}yr)")
        print(f"  Max DD: {metrics.get('max_drawdown_r', 'N/A')}R | Max Win Streak: {metrics.get('max_win_streak', 'N/A')}")
        print(f"  Profit Factor: {metrics.get('profit_factor', 'N/A')} | Avg Hold: {metrics.get('avg_hold_hours', 'N/A')}h")

        # Signal breakdown
        if stats.get("by_signal"):
            print("  Signal Breakdown:")
            for sig, s in stats["by_signal"].items():
                wr = round(s["wins"] / s["total"] * 100, 1) if s["total"] > 0 else 0
                print(f"    {sig}: {s['total']} trades, WR={wr}%, R={s['total_r']:+.2f}")

    # -----------------------------------------------------------------------
    # Titan analysis
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("⚡ TITAN STRATEGY — Multi-Timeframe Analysis")
    print("=" * 70)

    for tf, limit in TITAN_TIMEFRAMES:
        key = f"titan_{tf}"
        data = all_data.get(key, {})
        df = data.get("df", pd.DataFrame())

        print(f"\n--- {tf} ---")
        print(f"  Candles: {len(df)}")

        if df.empty or len(df) < WARMUP + 10:
            print("  ⚠ Insufficient data, skipping")
            continue

        # Add indicators
        titan._add_indicators(df)

        # Run backtest
        bt = titan_backtest(df, tf)
        stats = bt["stats"]
        trades = bt.get("trades", [])

        if "error" in bt:
            print(f"  ⚠ Error: {bt['error']}")
            continue

        # Advanced metrics
        metrics = compute_trade_metrics(trades)
        years = time_in_year_fraction(df)
        ann_r = annualized_return(stats["total_r"], years)

        result = {
            "timeframe": tf,
            "data_range_years": round(years, 2),
            **stats,
            **metrics,
            "annualized_r": round(ann_r, 2),
        }
        results["titan"].append(result)

        # Print
        print(f"  Signals: {stats['total_signals']} | Trades: {stats['total_trades']}")
        print(f"  Win Rate: {stats['win_rate']}%")
        print(f"  Longs: {stats.get('longs', 0)} (W={stats.get('long_wins', 0)}) | Shorts: {stats.get('shorts', 0)} (W={stats.get('short_wins', 0)})")
        print(f"  Total R: {stats['total_r']:+.2f}R | EV/Trade: {stats['ev_per_trade']:.3f}R")
        print(f"  PnL%: {stats['total_pnl_pct']:+.2f}%")
        print(f"  Annualized R: {ann_r:+.2f}R/yr (data: {years:.1f}yr)")
        print(f"  Max DD: {metrics.get('max_drawdown_r', 'N/A')}R | Max Win Streak: {metrics.get('max_win_streak', 'N/A')}")
        print(f"  Profit Factor: {metrics.get('profit_factor', 'N/A')} | Avg Hold: {metrics.get('avg_hold_hours', 'N/A')}h")

        if stats.get("by_signal"):
            print("  Signal Breakdown:")
            for sig, s in stats["by_signal"].items():
                wr = round(s["wins"] / s["total"] * 100, 1) if s["total"] > 0 else 0
                print(f"    {sig}: {s['total']} trades, WR={wr}%, R={s['total_r']:+.2f}")

    # -----------------------------------------------------------------------
    # Summary & Recommendation
    # -----------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 SUMMARY & RECOMMENDATION")
    print("=" * 70)

    # Rank Oracle configs by EV
    oracle_ranked = sorted(results["oracle"], key=lambda x: x.get("ev_per_trade", -999) or -999, reverse=True)
    titan_ranked = sorted(results["titan"], key=lambda x: x.get("ev_per_trade", -999) or -999, reverse=True)

    print("\n--- Oracle Ranking (by EV/Trade) ---")
    for i, r in enumerate(oracle_ranked):
        ev = r.get("ev_per_trade")
        wr = r.get("win_rate")
        total = r.get("total_trades")
        ann = r.get("annualized_r")
        dd = r.get("max_drawdown_r")
        print(f"  {i+1}. {r['config']:15s} | EV={ev:+.3f}R | WR={wr}% | Trades={total} | Ann.R={ann:+.2f} | MaxDD={dd}R")

    print("\n--- Titan Ranking (by EV/Trade) ---")
    for i, r in enumerate(titan_ranked):
        ev = r.get("ev_per_trade")
        wr = r.get("win_rate")
        total = r.get("total_trades")
        ann = r.get("annualized_r")
        dd = r.get("max_drawdown_r")
        print(f"  {i+1}. {r['timeframe']:5s} | EV={ev:+.3f}R | WR={wr}% | Trades={total} | Ann.R={ann:+.2f} | MaxDD={dd}R")

    # Best overall
    best_oracle = oracle_ranked[0] if oracle_ranked else None
    best_titan = titan_ranked[0] if titan_ranked else None

    print("\n--- 🏆 BEST CONFIGURATION ---")
    if best_oracle and best_titan:
        oracle_ev = best_oracle.get("ev_per_trade") or -999
        titan_ev = best_titan.get("ev_per_trade") or -999

        if oracle_ev > titan_ev:
            print(f"  Strategy: ORACLE on {best_oracle['config']}")
            print(f"  EV/Trade: {oracle_ev:+.3f}R | WR: {best_oracle['win_rate']}% | Ann.R: {best_oracle['annualized_r']:+.2f}")
        else:
            print(f"  Strategy: TITAN on {best_titan['timeframe']}")
            print(f"  EV/Trade: {titan_ev:+.3f}R | WR: {best_titan['win_rate']}% | Ann.R: {best_titan['annualized_r']:+.2f}")

    # Export results to JSON
    output_path = "/tmp/btc_timeframe_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📁 Full results saved to: {output_path}")

    return results


if __name__ == "__main__":
    asyncio.run(run_analysis())
