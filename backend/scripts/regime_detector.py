"""
Regime Detector + Regime-Switching Backtest
=============================================
Tests: "HODL in bull, trade shorts in bear" vs pure HODL vs pure trading.

Regime detection methods:
1. BTC Daily EMA200 (simple, classic)
2. BTC Daily ADX + direction
3. BTC 4H trend structure (higher highs/lower lows)

Usage:
    docker compose exec backend python -m scripts.regime_detector
"""

import asyncio, sys
from datetime import datetime, timezone
import pandas as pd
import numpy as np

sys.path.insert(0, "/app")
from app.trading.backtest_engine import load_candles
from app.strategies.titan import TitanStrategy

titan = TitanStrategy()
WARMUP = 200


def detect_regime_btc_ema(df_1d):
    """
    Simple regime: BTC daily close vs EMA200.
    Above = BULL, Below = BEAR.
    """
    titan._add_indicators(df_1d)
    regimes = []
    for i in range(len(df_1d)):
        row = df_1d.iloc[i]
        ema = row.get("ema200")
        price = row["close"]
        if pd.isna(ema):
            regimes.append("UNKNOWN")
        elif price > ema:
            regimes.append("BULL")
        else:
            regimes.append("BEAR")
    df_1d["regime"] = regimes
    return df_1d


def detect_regime_btc_adx(df_1d):
    """
    ADX-based: ADX>25 + price>EMA200 = STRONG_BULL
    ADX>25 + price<EMA200 = STRONG_BEAR
    ADX<25 = CHOPPY
    """
    regimes = []
    for i in range(len(df_1d)):
        row = df_1d.iloc[i]
        ema = row.get("ema200")
        adx = row.get("adx")
        price = row["close"]
        if pd.isna(ema) or pd.isna(adx):
            regimes.append("UNKNOWN")
        elif adx > 25 and price > ema:
            regimes.append("STRONG_BULL")
        elif adx > 25 and price < ema:
            regimes.append("STRONG_BEAR")
        else:
            regimes.append("CHOPPY")
    df_1d["regime_adx"] = regimes
    return df_1d


def detect_regime_4h_structure(df_4h, lookback=50):
    """
    4H trend structure: compare current price to rolling high/low.
    Price within top 25% of recent range = BULL
    Price within bottom 25% of recent range = BEAR
    Middle 50% = CHOPPY
    """
    roll_high = df_4h["high"].rolling(lookback).max()
    roll_low = df_4h["low"].rolling(lookback).min()
    regimes = []
    for i in range(len(df_4h)):
        price = df_4h.iloc[i]["close"]
        h = roll_high.iloc[i]
        l = roll_low.iloc[i]
        if pd.isna(h) or pd.isna(l) or h == l:
            regimes.append("UNKNOWN")
            continue
        pct = (price - l) / (h - l)
        if pct > 0.75:
            regimes.append("BULL")
        elif pct < 0.25:
            regimes.append("BEAR")
        else:
            regimes.append("CHOPPY")
    df_4h["regime_structure"] = regimes
    return df_4h


def regime_at_timestamp(ts_ms, df_1d, col="regime"):
    """Get the regime at a given timestamp from daily data."""
    mask = df_1d["ts_ms"] <= ts_ms
    if not mask.any():
        return "UNKNOWN"
    row = df_1d[mask].iloc[-1]
    return row.get(col, "UNKNOWN")


def run_titan(df_4h, sl=1.5, tp=0, mc=55):
    """Run Titan backtest, return trades with regime labels."""
    if df_4h.empty or len(df_4h) < WARMUP+10:
        return []
    trades, active = [], None
    for i in range(WARMUP, len(df_4h)):
        row = df_4h.iloc[i]
        price = float(row["close"])
        if active:
            h, l = float(row["high"]), float(row["low"])
            r = None
            if active["t"]=="LONG":
                if l<=active["sl"]: r="LOSS"
                elif h>=active["tp"]: r="WIN"
            else:
                if h>=active["sl"]: r="LOSS"
                elif l<=active["tp"]: r="WIN"
            if r: active["r"]=r; trades.append(active); active=None; continue
        if pd.isna(row.get("rsi")) or pd.isna(row.get("ema200")): continue
        ema=row.get("ema200"); trend="BULLISH" if not pd.isna(ema) and price>ema else "BEARISH"
        mom=titan._analyze_momentum(row); vol=titan._analyze_volatility(row)
        rw=df_4h.iloc[max(0,i-4):i+1]
        bs=rw[rw["sweep_type"]=="bullish"]; rs="bullish" if not bs.empty else ("bearish" if not rw[rw["sweep_type"]=="bearish"].empty else None)
        t=titan._generate_signal(trend,mom,vol,row,rs); sig,conf=t["type"],t["confidence"]
        il=sig in ("BUY","BUY_LIMIT"); is_=sig in ("SELL","SELL_LIMIT")
        if not(il or is_) or conf<mc: continue
        if active and active["t"]==("LONG" if il else "SHORT"): continue
        a=float(row.get("atr",0))
        if a<=0: continue
        adx_val=row.get("adx")
        tm=tp if tp>0 else (3.0 if(adx_val is not None and not pd.isna(adx_val) and adx_val>40) else 2.0)
        if il: sl_=price-a*sl; tp_=price+a*tm; d="LONG"
        else: sl_=price+a*sl; tp_=price-a*tm; d="SHORT"
        active={"t":d,"e":price,"sl":sl_,"tp":tp_,"ts":row["ts_ms"],"idx":i}
    return trades


def stats(trades):
    n=len(trades); w=sum(1 for t in trades if t["r"]=="WIN"); l=n-w
    wr=w/n*100 if n else 0
    tr=0
    for t in trades:
        r=abs(t["e"]-t["sl"]); rw=abs(t["tp"]-t["e"]); rr=rw/r if r>0 else 0
        tr+=rr if t["r"]=="WIN" else -1
    ev=tr/n if n else 0
    eq=[0.0]
    for t in trades:
        r=abs(t["e"]-t["sl"]); rw=abs(t["tp"]-t["e"]); rr=rw/r if r else 0
        eq.append(eq[-1]+(rr if t["r"]=="WIN" else -1))
    pk=0; mdd=0
    for e in eq: pk=max(pk,e); mdd=max(mdd,pk-e)
    return {"n":n,"w":w,"l":l,"wr":round(wr,1),"r":round(tr,2),"ev":round(ev,3),"mdd":round(mdd,2),"pf":round(w/max(l,1),2)}


async def run():
    print("="*70)
    print("REGIME DETECTOR + SWITCHING STRATEGY")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("="*70)

    btc_4h = await load_candles("BTC/USDT", "4h")
    btc_1d = await load_candles("BTC/USDT", "1d")
    eth_4h = await load_candles("ETH/USDT", "4h")

    # Cap for speed
    MAX = 1500
    if len(btc_4h)>MAX: btc_4h=btc_4h.iloc[-MAX:].reset_index(drop=True)
    if len(eth_4h)>MAX: eth_4h=eth_4h.iloc[-MAX:].reset_index(drop=True)

    for df in [btc_4h, eth_4h]:
        titan._add_indicators(df)

    # Detect regimes
    btc_1d = detect_regime_btc_ema(btc_1d)
    btc_1d = detect_regime_btc_adx(btc_1d)

    def y(df): return (df.iloc[-1]["ts_ms"]-df.iloc[0]["ts_ms"])/(365.25*24*3600*1000)

    # ================================================================
    # 1. Regime distribution
    # ================================================================
    print("\n"+"="*70)
    print("1. REGIME DISTRIBUTION (BTC Daily)")
    print("="*70)

    regime_counts = btc_1d["regime"].value_counts()
    total = len(btc_1d)
    print(f"\n  EMA200 method ({total} daily candles):")
    for reg, cnt in regime_counts.items():
        print(f"    {reg:12s}: {cnt:>4} days ({cnt/total*100:.1f}%)")

    regime_adx_counts = btc_1d["regime_adx"].value_counts()
    print(f"\n  ADX method:")
    for reg, cnt in regime_adx_counts.items():
        print(f"    {reg:12s}: {cnt:>4} days ({cnt/total*100:.1f}%)")

    # Show dates
    print(f"\n  Date range: {btc_1d.iloc[0]['timestamp']} to {btc_1d.iloc[-1]['timestamp']}")

    # Find regime transitions
    transitions = []
    for i in range(1, len(btc_1d)):
        prev = btc_1d.iloc[i-1]["regime"]
        curr = btc_1d.iloc[i]["regime"]
        if prev != curr:
            transitions.append({
                "date": btc_1d.iloc[i]["timestamp"],
                "from": prev,
                "to": curr,
                "price": btc_1d.iloc[i]["close"]
            })
    print(f"\n  Regime transitions ({len(transitions)}):")
    for t in transitions:
        print(f"    {str(t['date'])[:10]}: {t['from']} -> {t['to']} @ ${t['price']:,.0f}")

    # ================================================================
    # 2. Titan performance BY regime
    # ================================================================
    print("\n"+"="*70)
    print("2. TITAN PERFORMANCE BY REGIME")
    print("="*70)

    # BTC-opt trades
    trades_btc = run_titan(btc_4h, sl=1.75, tp=4.0, mc=55)
    # Label each trade with regime
    for t in trades_btc:
        t["regime"] = regime_at_timestamp(t["ts"], btc_1d, "regime")
        t["regime_adx"] = regime_at_timestamp(t["ts"], btc_1d, "regime_adx")

    # Split by regime
    print(f"\n  BTC Titan (SL=1.75, TP=4.0): {len(trades_btc)} total trades")
    for reg in ["BULL", "BEAR"]:
        reg_trades = [t for t in trades_btc if t["regime"]==reg]
        s = stats(reg_trades)
        if s["n"]==0: continue
        print(f"    {reg}: {s['n']} trades WR={s['wr']}% EV={s['ev']:+.3f}R R={s['r']:+.2f} PF={s['pf']}")

    # By ADX regime
    print(f"\n  By ADX regime:")
    for reg in ["STRONG_BULL", "STRONG_BEAR", "CHOPPY"]:
        reg_trades = [t for t in trades_btc if t["regime_adx"]==reg]
        s = stats(reg_trades)
        if s["n"]==0: continue
        print(f"    {reg:12s}: {s['n']:>3} trades WR={s['wr']}% EV={s['ev']:+.3f}R R={s['r']:+.2f}")

    # Long vs Short by regime
    print(f"\n  Longs vs Shorts by regime:")
    for reg in ["BULL", "BEAR"]:
        longs = [t for t in trades_btc if t["regime"]==reg and t["t"]=="LONG"]
        shorts = [t for t in trades_btc if t["regime"]==reg and t["t"]=="SHORT"]
        ls = stats(longs); ss = stats(shorts)
        if ls["n"]>0: print(f"    {reg} LONGS:  {ls['n']} trades WR={ls['wr']}% EV={ls['ev']:+.3f}R")
        if ss["n"]>0: print(f"    {reg} SHORTS: {ss['n']} trades WR={ss['wr']}% EV={ss['ev']:+.3f}R")

    # ================================================================
    # 3. ETH performance by regime
    # ================================================================
    print("\n"+"="*70)
    print("3. ETH PERFORMANCE BY REGIME")
    print("="*70)

    trades_eth = run_titan(eth_4h, sl=1.5, tp=4.0, mc=55)
    for t in trades_eth:
        t["regime"] = regime_at_timestamp(t["ts"], btc_1d, "regime")

    print(f"\n  ETH Titan (SL=1.5, TP=4.0): {len(trades_eth)} total trades")
    for reg in ["BULL", "BEAR"]:
        reg_trades = [t for t in trades_eth if t["regime"]==reg]
        s = stats(reg_trades)
        if s["n"]==0: continue
        print(f"    {reg}: {s['n']} trades WR={s['wr']}% EV={s['ev']:+.3f}R R={s['r']:+.2f}")

    # ================================================================
    # 4. Regime-switching strategy
    # ================================================================
    print("\n"+"="*70)
    print("4. REGIME-SWITCHING: HODL in BULL, Trade in BEAR")
    print("="*70)

    # Simulate: during BULL regime, track BTC price (HODL). During BEAR, use Titan shorts.
    # Walk through 4H candles, track equity
    equity_hodl = [0.0]  # Pure HODL
    equity_trade = [0.0]  # Pure Titan
    equity_switch = [0.0]  # Regime-switching

    # For HODL: just track price change
    price_start = float(btc_4h.iloc[WARMUP]["close"])

    # For trading: accumulate R from trades
    # For switching: HODL in BULL, short trades in BEAR

    # Simple approach: walk through each candle, determine regime, accumulate returns
    prev_price = price_start
    hodl_equity = 0.0
    trade_equity = 0.0
    switch_equity = 0.0

    # Map trades to their exit candles for quick lookup
    trade_exits = {}
    for t in trades_btc:
        idx = t.get("idx", 0)
        if idx not in trade_exits:
            trade_exits[idx] = []
        trade_exits[idx].append(t)

    active_trade = None
    active_switch = None

    for i in range(WARMUP, len(btc_4h)):
        row = btc_4h.iloc[i]
        price = float(row["close"])
        ts = row["ts_ms"]
        regime = regime_at_timestamp(ts, btc_1d, "regime")

        # HODL equity: price change from start
        hodl_equity = (price - price_start) / price_start

        # Trade equity: from Titan trades that exit at this candle
        # (simplified: accumulate from resolved trades)

        # Track regime switches for HODL/short logic
        # Simple: BULL = hold BTC spot, BEAR = hold short (inverse BTC)
        candle_ret = (price - prev_price) / prev_price if prev_price > 0 else 0
        if regime == "BULL":
            switch_equity += candle_ret  # Long: gain when price goes up
        elif regime == "BEAR":
            switch_equity -= candle_ret  # Short: gain when price goes down

        prev_price = price

    # Trade equity from actual trades
    for t in trades_btc:
        risk = abs(t["e"]-t["sl"])
        rew = abs(t["tp"]-t["e"])
        rr = rew/risk if risk>0 else 0
        if t["r"]=="WIN": trade_equity += rr
        else: trade_equity -= 1

    hodl_pct = hodl_equity * 100
    trade_pct = trade_equity * 100  # At 1% risk
    switch_pct = switch_equity * 100
    y_btc = y(btc_4h)

    print(f"\n  Period: {y_btc:.2f}yr (${price_start:,.0f} -> ${btc_4h.iloc[-1]['close']:,.0f})")
    print(f"\n  Strategy              | Return  | Ann.    | How")
    print(f"  ----------------------|---------|---------|----")
    print(f"  HODL (buy & hold)     | {hodl_pct:>+6.1f}% | {hodl_pct/y_btc:>+6.1f}% | Always long BTC")
    print(f"  Titan (SL=1.75 TP=4)  | {trade_pct:>+6.1f}% | {trade_pct/y_btc:>+6.1f}% | Always trading (1% risk/trade)")
    print(f"  Regime-switch         | {switch_pct:>+6.1f}% | {switch_pct/y_btc:>+6.1f}% | HODL in BULL, short in BEAR")

    # ================================================================
    # 5. The real question: can we PREDICT regime changes?
    # ================================================================
    print("\n"+"="*70)
    print("5. REGIME PREDICTION ACCURACY")
    print("="*70)

    # How often does the regime stay the same day-to-day?
    same = 0
    changed = 0
    for i in range(1, len(btc_1d)):
        if btc_1d.iloc[i]["regime"] == btc_1d.iloc[i-1]["regime"]:
            same += 1
        else:
            changed += 1
    total_days = same + changed
    print(f"\n  Daily regime persistence: {same}/{total_days} days ({same/total_days*100:.1f}%) stayed the same")
    print(f"  Regime changes: {changed} times in {total_days} days (~1 change every {total_days/max(changed,1):.0f} days)")

    # After a regime change, how long does it last?
    streaks = []
    current = btc_1d.iloc[0]["regime"]
    streak = 1
    for i in range(1, len(btc_1d)):
        if btc_1d.iloc[i]["regime"] == current:
            streak += 1
        else:
            streaks.append({"regime": current, "days": streak})
            current = btc_1d.iloc[i]["regime"]
            streak = 1
    streaks.append({"regime": current, "days": streak})

    bull_streaks = [s["days"] for s in streaks if s["regime"]=="BULL"]
    bear_streaks = [s["days"] for s in streaks if s["regime"]=="BEAR"]
    print(f"\n  Average BULL streak: {np.mean(bull_streaks):.0f} days (min={min(bull_streaks)}, max={max(bull_streaks)})")
    print(f"  Average BEAR streak: {np.mean(bear_streaks):.0f} days (min={min(bear_streaks)}, max={max(bear_streaks)})")

    # Best simple predictor: if BTC is above EMA200 and EMA200 is rising, likely BULL continues
    print(f"\n  Simplest reliable signal: BTC Daily close vs EMA200")
    print(f"  Above EMA200 -> BULL regime (HODL or longs only)")
    print(f"  Below EMA200 -> BEAR regime (shorts or stay in cash)")
    print(f"  EMA200 is a LAGGING indicator - you'll miss the first few % of each move")
    print(f"  But regimes last {np.mean(bull_streaks):.0f}-{np.mean(bear_streaks):.0f} days on average, so you catch most of it")


if __name__=="__main__":
    asyncio.run(run())
