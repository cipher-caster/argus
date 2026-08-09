"""
ETH Full Analysis — Multi-Timeframe + Parameter Sweep + HODL Comparison
=========================================================================
Same analysis as BTC but for ETH. All three assessments in one run.

Usage:
    docker compose exec backend python -m scripts.eth_full_analysis
"""

import asyncio
import sys
import json
from datetime import datetime, timezone
from itertools import product

import pandas as pd
import numpy as np
import ccxt.async_support as ccxt

sys.path.insert(0, "/app")
from app.strategies.oracle import OracleStrategy
from app.strategies.titan import TitanStrategy

oracle = OracleStrategy()
titan = TitanStrategy()

SYMBOL = "ETH/USDT"
WARMUP = 200


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

async def fetch_candles(exchange, symbol, timeframe, limit):
    print(f"  {symbol} {timeframe} (limit={limit})...")
    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp","open","high","low","close","volume"])
    df["ts_ms"] = df["timestamp"]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df


# ---------------------------------------------------------------------------
# HODL
# ---------------------------------------------------------------------------

def hodl_metrics(df):
    start = float(df.iloc[0]["close"])
    end = float(df.iloc[-1]["close"])
    total_ret = (end - start) / start
    peak = df["close"].expanding().max()
    dd = (df["close"] - peak) / peak
    max_dd = abs(dd.min())
    years = (df.iloc[-1]["ts_ms"] - df.iloc[0]["ts_ms"]) / (365.25 * 24 * 3600 * 1000)
    ann_ret = (1 + total_ret) ** (1 / years) - 1 if years > 0 else 0
    return {
        "start": round(start, 2), "end": round(end, 2),
        "total_ret_pct": round(total_ret * 100, 2),
        "ann_ret_pct": round(ann_ret * 100, 2),
        "max_dd_pct": round(max_dd * 100, 2),
        "years": round(years, 2),
    }


# ---------------------------------------------------------------------------
# Oracle backtest
# ---------------------------------------------------------------------------

def oracle_backtest(df_micro, df_macro):
    if df_micro.empty or df_macro.empty:
        return {"trades": [], "stats": {"error": "empty data"}}
    trades = []
    active = None
    macro_biases = {}
    for _, row in df_macro.iterrows():
        macro_biases[row["timestamp"]] = oracle._calculate_macro_bias(row)

    for i in range(WARMUP, len(df_micro)):
        row = df_micro.iloc[i]
        if active:
            h, l = float(row["high"]), float(row["low"])
            result = None
            if active["t"] == "LONG":
                if l <= active["sl"]: result = "LOSS"
                elif h >= active["tp"]: result = "WIN"
            else:
                if h >= active["sl"]: result = "LOSS"
                elif l <= active["tp"]: result = "WIN"
            if result:
                active["r"] = result
                trades.append(active)
                active = None
                continue
        if pd.isna(row.get("rsi")) or pd.isna(row.get("ema200")):
            continue
        ts = row["timestamp"]
        macro_ts = [t for t in macro_biases if t <= ts]
        if not macro_ts:
            continue
        m_bias = macro_biases[max(macro_ts)]
        e_score = oracle._calculate_earnest_score(row)["score"]
        sig = oracle._synthesize_signal(e_score, m_bias["score"])
        if sig not in ("STRONG_BUY", "BUY", "STRONG_SELL", "SELL"):
            continue
        atr = float(row["atr"]) if not pd.isna(row.get("atr")) else float(row["close"]) * 0.01
        price = float(row["close"])
        if "BUY" in sig:
            active = {"t": "LONG", "e": price, "tp": price + atr * 3.0, "sl": price - atr * 1.5, "sig": sig}
        elif "SELL" in sig:
            active = {"t": "SHORT", "e": price, "tp": price - atr * 3.0, "sl": price + atr * 1.5, "sig": sig}

    n = len(trades)
    w = sum(1 for t in trades if t["r"] == "WIN")
    total_r = sum(
        (abs(t["tp"] - t["e"]) / abs(t["e"] - t["sl"]) if t["r"] == "WIN" else -1)
        for t in trades if abs(t["e"] - t["sl"]) > 0
    )
    ev = total_r / n if n else 0
    return {"trades": trades, "stats": {"trades": n, "wins": w, "wr": round(w/n*100,1) if n else 0, "total_r": round(total_r,2), "ev": round(ev,3)}}


# ---------------------------------------------------------------------------
# Titan backtest
# ---------------------------------------------------------------------------

def titan_backtest(df, sl_mult=1.5, tp_mult=0, min_conf=55):
    if df.empty or len(df) < WARMUP + 10:
        return {"trades": [], "stats": {"error": "insufficient data"}}
    trades = []
    active = None
    for i in range(WARMUP, len(df)):
        row = df.iloc[i]
        price = float(row["close"])
        if active:
            h, l = float(row["high"]), float(row["low"])
            result = None
            if active["t"] == "LONG":
                if l <= active["sl"]: result = "LOSS"
                elif h >= active["tp"]: result = "WIN"
            else:
                if h >= active["sl"]: result = "LOSS"
                elif l <= active["tp"]: result = "WIN"
            if result:
                pnl = (active["tp"] - active["e"]) / active["e"] if result == "WIN" else (active["sl"] - active["e"]) / active["e"]
                if active["t"] == "SHORT": pnl = -pnl
                active["r"] = result
                active["pnl"] = pnl
                active["exit_ts"] = row["ts_ms"]
                active["bars"] = i - active["idx"]
                trades.append(active)
                active = None
                continue
        if pd.isna(row.get("rsi")) or pd.isna(row.get("ema200")):
            continue
        ema = row.get("ema200")
        trend = "BULLISH" if not pd.isna(ema) and price > ema else "BEARISH"
        mom = titan._analyze_momentum(row)
        vol = titan._analyze_volatility(df.iloc[max(0, i - titan.squeeze_lookback + 1) : i + 1])
        rw = df.iloc[max(0,i-4):i+1]
        bs = rw[rw["sweep_type"] == "bullish"]
        rs = "bullish" if not bs.empty else ("bearish" if not rw[rw["sweep_type"] == "bearish"].empty else None)
        t = titan._generate_signal(trend, mom, vol, row, rs)
        sig, conf = t["type"], t["confidence"]
        is_long = sig in ("BUY", "BUY_LIMIT")
        is_short = sig in ("SELL", "SELL_LIMIT")
        if not (is_long or is_short) or conf < min_conf:
            continue
        if active and active["t"] == ("LONG" if is_long else "SHORT"):
            continue
        atr = float(row.get("atr", 0))
        if atr <= 0: continue
        tp_m = tp_mult if tp_mult > 0 else (3.0 if (not pd.isna(row.get("adx", 25)) and row["adx"] > 40) else 2.0)
        if is_long:
            sl, tp = price - atr * sl_mult, price + atr * tp_m
            direction = "LONG"
        else:
            sl, tp = price + atr * sl_mult, price - atr * tp_m
            direction = "SHORT"
        active = {"t": direction, "e": price, "sl": sl, "tp": tp, "ts": row["ts_ms"], "idx": i, "sig": sig}

    n = len(trades)
    w = sum(1 for t in trades if t["r"] == "WIN")
    l = n - w
    wr = w / n * 100 if n else 0
    total_r = sum(
        (abs(t["tp"] - t["e"]) / abs(t["e"] - t["sl"]) if t["r"] == "WIN" else -1)
        for t in trades if abs(t["e"] - t["sl"]) > 0
    )
    ev = total_r / n if n else 0
    longs = [t for t in trades if t["t"] == "LONG"]
    shorts = [t for t in trades if t["t"] == "SHORT"]
    eq = [0.0]
    for t in trades:
        r = abs(t["tp"]-t["e"])/abs(t["e"]-t["sl"]) if abs(t["e"]-t["sl"])>0 else 0
        eq.append(eq[-1]+(r if t["r"]=="WIN" else -1))
    pk = 0; mdd = 0
    for e in eq: pk = max(pk, e); mdd = max(mdd, pk-e)
    return {"trades": trades, "stats": {
        "trades": n, "wins": w, "losses": l, "wr": round(wr,1),
        "total_r": round(total_r,2), "ev": round(ev,3), "max_dd": round(mdd,2),
        "pf": round(w/max(l,1),2),
        "longs": len(longs), "long_wins": sum(1 for t in longs if t["r"]=="WIN"),
        "shorts": len(shorts), "short_wins": sum(1 for t in shorts if t["r"]=="WIN"),
    }}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run():
    print("=" * 70)
    print("ETH FULL ANALYSIS — Multi-Timeframe + Sweep + HODL vs Trade")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)

    exchange = ccxt.binance({"enableRateLimit": True})
    try:
        df_15m = await fetch_candles(exchange, SYMBOL, "15m", 1000)
        df_1h = await fetch_candles(exchange, SYMBOL, "1h", 1000)
        df_4h = await fetch_candles(exchange, SYMBOL, "4h", 1000)
        df_1d = await fetch_candles(exchange, SYMBOL, "1d", 500)
        # Macro data for Oracle
        df_4h_macro = await fetch_candles(exchange, SYMBOL, "4h", 1000)
        df_1d_macro = await fetch_candles(exchange, SYMBOL, "1d", 500)
        df_1w_macro = await fetch_candles(exchange, SYMBOL, "1w", 300)
    finally:
        await exchange.close()

    # Add indicators
    for df in [df_15m, df_1h, df_4h, df_1d, df_4h_macro, df_1d_macro, df_1w_macro]:
        oracle._add_indicators(df)
    for df in [df_15m, df_1h, df_4h, df_1d]:
        titan._add_indicators(df)

    def years(df):
        return (df.iloc[-1]["ts_ms"] - df.iloc[0]["ts_ms"]) / (365.25 * 24 * 3600 * 1000)

    # ================================================================
    # PART 1: Oracle Multi-Timeframe
    # ================================================================
    print("\n" + "=" * 70)
    print("1. ORACLE — Multi-Timeframe")
    print("=" * 70)

    oracle_configs = [
        ("15m/4h", df_15m, df_4h_macro),
        ("1h/1d", df_1h, df_1d_macro),
        ("4h/1w", df_4h, df_1w_macro),
        ("1d/1M", df_1d, df_1d_macro),
    ]
    for label, micro, macro in oracle_configs:
        r = oracle_backtest(micro, macro)
        s = r["stats"]
        y = years(micro)
        if "error" in s:
            print(f"  {label}: Error - {s['error']}")
            continue
        ann = s["total_r"] / y if y > 0 else 0
        print(f"  {label}: Trades={s['trades']} WR={s['wr']}% EV={s['ev']:+.3f}R TotalR={s['total_r']:+.2f} Ann.R={ann:+.2f}")

    # ================================================================
    # PART 2: Titan Multi-Timeframe
    # ================================================================
    print("\n" + "=" * 70)
    print("2. TITAN — Multi-Timeframe (default params)")
    print("=" * 70)

    titan_configs = [("15m", df_15m), ("1h", df_1h), ("4h", df_4h), ("1d", df_1d)]
    for label, df in titan_configs:
        r = titan_backtest(df)
        s = r["stats"]
        y = years(df)
        if "error" in s:
            print(f"  {label}: Error - {s['error']}")
            continue
        ann = s["total_r"] / y if y > 0 else 0
        print(f"  {label}: Trades={s['trades']} WR={s['wr']}% EV={s['ev']:+.3f}R TotalR={s['total_r']:+.2f} "
              f"MaxDD={s['max_dd']}R L={s['longs']}({s['long_wins']}W) S={s['shorts']}({s['short_wins']}W) "
              f"Ann.R={ann:+.2f}")

    # ================================================================
    # PART 3: Titan Parameter Sweep on 4H (most data)
    # ================================================================
    print("\n" + "=" * 70)
    print("3. TITAN PARAMETER SWEEP — 4H")
    print("=" * 70)

    y4h = years(df_4h)
    print(f"  Data: {len(df_4h)} candles, {y4h:.2f}yr\n")

    sls = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
    tps = [0, 1.5, 2.0, 2.5, 3.0, 4.0]
    mcs = [50, 55, 60, 65, 70]
    sweep = []
    for sl, tp, mc in product(sls, tps, mcs):
        r = titan_backtest(df_4h, sl_mult=sl, tp_mult=tp, min_conf=mc)
        s = r["stats"]
        if "error" in s or s["trades"] < 5:
            continue
        ann = s["total_r"] / y4h if y4h > 0 else 0
        sweep.append({"sl": sl, "tp": tp if tp > 0 else "adapt", "mc": mc, "ann": round(ann,2), **s})

    sweep.sort(key=lambda x: x["ev"], reverse=True)
    print(f"  {'#':>3} {'SL':>5} {'TP':>7} {'MC':>3} {'N':>4} {'WR':>5} {'EV':>7} {'R':>7} {'MDD':>5} {'PF':>5} {'Ann':>7}")
    print("  " + "-" * 65)
    for i, r in enumerate(sweep[:20]):
        tp = str(r["tp"])
        print(f"  {i+1:>3} {r['sl']:>5.2f} {tp:>7} {r['mc']:>3} {r['trades']:>4} {r['wr']:>5}% "
              f"{r['ev']:>+7.3f} {r['total_r']:>+7.2f} {r['max_dd']:>5.1f} {r['pf']:>5.2f} {r['ann']:>+7.2f}")

    best = sweep[0] if sweep else None
    if best:
        print(f"\n  Best: SL={best['sl']} TP={best['tp']} MC={best['mc']} -> EV={best['ev']:+.3f} WR={best['wr']}%")

    # ================================================================
    # PART 4: HODL vs Trading
    # ================================================================
    print("\n" + "=" * 70)
    print("4. HODL vs TRADING")
    print("=" * 70)

    h4 = hodl_metrics(df_4h)
    h1d = hodl_metrics(df_1d)
    print(f"\n  HODL 4H ({h4['years']}yr): {h4['start']:,.0f} -> {h4['end']:,.0f} = {h4['total_ret_pct']:+.1f}% (ann {h4['ann_ret_pct']:+.1f}%), DD={h4['max_dd_pct']}%")
    print(f"  HODL 1D ({h1d['years']}yr): {h1d['start']:,.0f} -> {h1d['end']:,.0f} = {h1d['total_ret_pct']:+.1f}% (ann {h1d['ann_ret_pct']:+.1f}%), DD={h1d['max_dd_pct']}%")

    print(f"\n  Trading configs (4H period):")
    trade_configs = [
        ("Default SL=1.5 adapt", 1.5, 0, 55),
        ("Wider SL=1.75 TP=3.0", 1.75, 3.0, 55),
        ("Wider SL=2.0 TP=4.0", 2.0, 4.0, 55),
    ]
    if best:
        trade_configs.append((f"Best sweep (SL={best['sl']} TP={best['tp']} MC={best['mc']})", best["sl"], 0 if best["tp"]=="adapt" else best["tp"], best["mc"]))

    for label, sl, tp, mc in trade_configs:
        r = titan_backtest(df_4h, sl_mult=sl, tp_mult=tp, min_conf=mc)
        s = r["stats"]
        if "error" in s:
            continue
        ann = s["total_r"] / y4h if y4h > 0 else 0
        ret_dd = ann / (s["max_dd"] / y4h) if s["max_dd"] > 0 and y4h > 0 else 0
        print(f"    {label:30s}: Ann={ann:+.1f}R MaxDD={s['max_dd']:.1f}R Score={ret_dd:.2f} Trades={s['trades']} WR={s['wr']}%")

    hodl_score = h4["ann_ret_pct"] / h4["max_dd_pct"] if h4["max_dd_pct"] > 0 else 0
    print(f"\n  HODL risk-adjusted score: {hodl_score:.2f}")

    # Leverage comparison
    print(f"\n  Leverage comparison (best Titan config):")
    if best:
        r = titan_backtest(df_4h, sl_mult=best["sl"], tp_mult=0 if best["tp"]=="adapt" else best["tp"], min_conf=best["mc"])
        s = r["stats"]
        for lev in [1, 3, 5]:
            ann_r = s["total_r"] / y4h if y4h > 0 else 0
            ann_pct = ann_r * 1.0 * lev  # 1% risk per trade
            dd_pct = s["max_dd"] * 1.0 * lev
            score = ann_pct / dd_pct if dd_pct > 0 else 0
            print(f"    {lev}x: Ann={ann_pct:+.1f}% MaxDD={dd_pct:.1f}% Score={score:.2f}")

    # Save
    output = {
        "hodl_4h": h4, "hodl_1d": h1d,
        "oracle_best": oracle_configs,
        "titan_sweep_top10": sweep[:10],
    }
    with open("/tmp/eth_analysis.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    print("\n  Saved to /tmp/eth_analysis.json")


if __name__ == "__main__":
    asyncio.run(run())
