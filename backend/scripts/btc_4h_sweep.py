"""
BTC 4H Parameter Sweep — the sweet spot with most data.
"""
import asyncio, sys, json
from itertools import product
import pandas as pd
import ccxt.async_support as ccxt

sys.path.insert(0, "/app")
from app.strategies.titan import TitanStrategy

titan = TitanStrategy()

def backtest(df, sl_mult, tp_mult, min_conf, warmup=200):
    if df.empty or len(df) < warmup + 10:
        return None
    trades = []
    active = None
    for i in range(warmup, len(df)):
        row = df.iloc[i]
        price = float(row["close"])
        if active:
            h, l = row["high"], row["low"]
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
        adx = row.get("adx", 25)
        tp_m = tp_mult if tp_mult > 0 else (3.0 if (not pd.isna(adx) and adx > 40) else 2.0)
        if is_long:
            sl = price - atr * sl_mult
            tp = price + atr * tp_m
        else:
            sl = price + atr * sl_mult
            tp = price - atr * tp_m
        active = {"t": "LONG" if is_long else "SHORT", "e": price, "tp": tp, "sl": sl}
    
    n = len(trades)
    w = sum(1 for t in trades if t["r"] == "WIN")
    l = n - w
    wr = w / n * 100 if n else 0
    total_r = 0
    for t in trades:
        risk = abs(t["e"] - t["sl"])
        rew = abs(t["tp"] - t["e"])
        rr = rew / risk if risk else 0
        total_r += rr if t["r"] == "WIN" else -1
    ev = total_r / n if n else 0
    
    # max dd
    eq = [0.0]
    for t in trades:
        risk = abs(t["e"] - t["sl"])
        rew = abs(t["tp"] - t["e"])
        rr = rew / risk if risk else 0
        eq.append(eq[-1] + (rr if t["r"] == "WIN" else -1))
    peak = 0
    mdd = 0
    for e in eq:
        peak = max(peak, e)
        mdd = max(mdd, peak - e)
    
    longs = [t for t in trades if t["t"] == "LONG"]
    shorts = [t for t in trades if t["t"] == "SHORT"]
    lw = sum(1 for t in longs if t["r"] == "WIN")
    sw = sum(1 for t in shorts if t["r"] == "WIN")
    
    return {"sl": sl_mult, "tp": tp_mult if tp_mult > 0 else "adapt", "mc": min_conf,
            "n": n, "w": w, "l": l, "wr": round(wr, 1), "r": round(total_r, 2),
            "ev": round(ev, 3), "mdd": round(mdd, 2), "pf": round(w/max(l,1), 2),
            "ln": len(longs), "lw": lw, "sn": len(shorts), "sw": sw}

async def run():
    print("=" * 70)
    print("BTC 4H PARAMETER SWEEP")
    print("=" * 70)
    
    ex = ccxt.binance({"enableRateLimit": True})
    try:
        ohlcv = await ex.fetch_ohlcv("BTC/USDT", "4h", limit=1000)
    finally:
        await ex.close()
    
    df = pd.DataFrame(ohlcv, columns=["timestamp","open","high","low","close","volume"])
    df["ts_ms"] = df["timestamp"]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    titan._add_indicators(df)
    
    years = (df.iloc[-1]["ts_ms"] - df.iloc[0]["ts_ms"]) / (365.25 * 24 * 3600 * 1000)
    print(f"\nData: {len(df)} candles, {years:.2f} years\n")
    
    sls = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
    tps = [0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    mcs = [50, 55, 60, 65, 70]
    
    results = []
    for sl, tp, mc in product(sls, tps, mcs):
        r = backtest(df, sl, tp, mc)
        if r and r["n"] >= 5:
            r["ann"] = round(r["r"] / years, 2) if years > 0 else 0
            results.append(r)
    
    results.sort(key=lambda x: x["ev"], reverse=True)
    
    print(f"{'#':>3} {'SL':>5} {'TP':>7} {'MC':>3} {'Trades':>6} {'WR':>5} "
          f"{'EV':>7} {'TotalR':>8} {'MDD':>5} {'PF':>5} {'Ann.R':>7} "
          f"{'L':>3}{'LWR':>4} {'S':>3}{'SWR':>4}")
    print("-" * 90)
    for i, r in enumerate(results[:25]):
        tp = str(r["tp"])
        lwr = f"{r['lw']}/{r['ln']}" if r["ln"] else "-"
        swr = f"{r['sw']}/{r['sn']}" if r["sn"] else "-"
        print(f"{i+1:>3} {r['sl']:>5.2f} {tp:>7} {r['mc']:>3} {r['n']:>6} {r['wr']:>5}% "
              f"{r['ev']:>+7.3f} {r['r']:>+8.2f} {r['mdd']:>5.1f} {r['pf']:>5.2f} {r['ann']:>+7.2f} "
              f"{lwr:>7} {swr:>7}")
    
    print("\n--- Best 1d configs applied to 4h data ---")
    best_1d = [r for r in results if r["sl"] >= 2.0 and r["mc"] >= 65]
    for r in best_1d[:5]:
        tp = str(r["tp"])
        print(f"  SL={r['sl']} TP={tp} MC={r['mc']}: EV={r['ev']:+.3f} WR={r['wr']}% Trades={r['n']}")

if __name__ == "__main__":
    asyncio.run(run())
