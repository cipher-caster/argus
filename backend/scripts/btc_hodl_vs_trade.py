"""
BTC: Futures vs Swing vs HODL — Head-to-Head Comparison
========================================================
Compares three approaches on the same BTC data:
1. HODL — buy and hold, no leverage
2. Swing — Titan signals, spot (1x leverage), risk-defined
3. Futures — Titan signals, leveraged (3x/5x/10x)

Also measures: max drawdown, time in market, Sharpe-like metric.

Usage:
    docker compose exec backend python -m scripts.btc_hodl_vs_trade
"""

import asyncio
import sys
import json
from datetime import datetime, timezone

import pandas as pd
import numpy as np
import ccxt.async_support as ccxt

sys.path.insert(0, "/app")

from app.strategies.titan import TitanStrategy

titan = TitanStrategy()
SYMBOL = "BTC/USDT"
WARMUP = 200


async def fetch_candles(exchange, symbol, timeframe, limit):
    print(f"  Fetching {symbol} {timeframe} (limit={limit})...")
    ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp","open","high","low","close","volume"])
    df["ts_ms"] = df["timestamp"]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df


def compute_hodl_metrics(df):
    """Buy-and-hold from first candle to last."""
    start_price = float(df.iloc[0]["close"])
    end_price = float(df.iloc[-1]["close"])
    total_return = (end_price - start_price) / start_price
    
    # Max drawdown on the close price series
    peak = df["close"].expanding().max()
    dd = (df["close"] - peak) / peak
    max_dd = abs(dd.min())
    
    # Time in market
    years = (df.iloc[-1]["ts_ms"] - df.iloc[0]["ts_ms"]) / (365.25 * 24 * 3600 * 1000)
    ann_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
    
    # How many days were "in drawdown > 10%?"
    dd_series = dd.abs()
    days_in_big_dd = (dd_series > 0.10).sum()
    pct_in_big_dd = days_in_big_dd / len(df) * 100
    
    return {
        "total_return_pct": round(total_return * 100, 2),
        "ann_return_pct": round(ann_return * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "years": round(years, 2),
        "start_price": round(start_price, 2),
        "end_price": round(end_price, 2),
        "pct_candles_in_10pct_dd": round(pct_in_big_dd, 1),
    }


def run_titan_trades(df, sl_mult=1.75, tp_mult=4.0, min_conf=55):
    """
    Walk-forward Titan with specific risk params.
    Returns list of trade dicts with entry/exit/pnl info.
    """
    trades = []
    active = None
    
    for i in range(WARMUP, len(df)):
        row = df.iloc[i]
        price = float(row["close"])
        
        if active:
            h, l = float(row["high"]), float(row["low"])
            result = None
            exit_price = None
            
            if active["dir"] == "LONG":
                if l <= active["sl"]:
                    result, exit_price = "LOSS", active["sl"]
                elif h >= active["tp"]:
                    result, exit_price = "WIN", active["tp"]
            else:
                if h >= active["sl"]:
                    result, exit_price = "LOSS", active["sl"]
                elif l <= active["tp"]:
                    result, exit_price = "WIN", active["tp"]
            
            if result:
                pnl_pct = (exit_price - active["entry"]) / active["entry"]
                if active["dir"] == "SHORT":
                    pnl_pct = -pnl_pct
                trades.append({
                    **active,
                    "result": result,
                    "exit": exit_price,
                    "exit_ts": row["ts_ms"],
                    "pnl_pct": pnl_pct,
                    "bars_held": i - active["entry_idx"],
                })
                active = None
                continue
        
        if pd.isna(row.get("rsi")) or pd.isna(row.get("ema200")):
            continue
        
        ema = row.get("ema200")
        trend = "BULLISH" if not pd.isna(ema) and price > ema else "BEARISH"
        mom = titan._analyze_momentum(row)
        vol = titan._analyze_volatility(row)
        rw = df.iloc[max(0,i-4):i+1]
        bs = rw[rw["sweep_type"] == "bullish"]
        rs = "bullish" if not bs.empty else ("bearish" if not rw[rw["sweep_type"] == "bearish"].empty else None)
        t = titan._generate_signal(trend, mom, vol, row, rs)
        sig, conf = t["type"], t["confidence"]
        is_long = sig in ("BUY", "BUY_LIMIT")
        is_short = sig in ("SELL", "SELL_LIMIT")
        if not (is_long or is_short) or conf < min_conf:
            continue
        if active and active["dir"] == ("LONG" if is_long else "SHORT"):
            continue
        
        atr = float(row.get("atr", 0))
        if atr <= 0:
            continue
        
        if is_long:
            sl = price - atr * sl_mult
            tp = price + atr * tp_mult
            direction = "LONG"
        else:
            sl = price + atr * sl_mult
            tp = price - atr * tp_mult
            direction = "SHORT"
        
        active = {
            "dir": direction,
            "entry": price,
            "sl": sl,
            "tp": tp,
            "entry_ts": row["ts_ms"],
            "entry_idx": i,
            "signal": sig,
        }
    
    return trades


def compute_trading_metrics(trades, leverage=1.0):
    """Compute portfolio-equity-style metrics for a series of trades."""
    if not trades:
        return None
    
    # Build equity curve (each trade risks 1R of capital)
    equity = [0.0]
    for t in trades:
        risk = abs(t["entry"] - t["sl"])
        reward = abs(t["tp"] - t["entry"])
        rr = reward / risk if risk > 0 else 0
        if t["result"] == "WIN":
            equity.append(equity[-1] + rr)
        else:
            equity.append(equity[-1] - 1.0)
    
    total_r = equity[-1]
    
    # Max drawdown in R
    peak = 0
    max_dd_r = 0
    for e in equity:
        peak = max(peak, e)
        max_dd_r = max(max_dd_r, peak - e)
    
    # Win rate
    wins = sum(1 for t in trades if t["result"] == "WIN")
    losses = sum(1 for t in trades if t["result"] == "LOSS")
    wr = wins / len(trades) * 100
    
    # Time in trades (% of total candles spent in a position)
    total_bars = sum(t["bars_held"] for t in trades)
    
    # Convert R to portfolio return at different leverages
    # If you risk 1% per trade at 1x leverage, total_r * 1% = portfolio return
    # At 5x leverage, risk per trade is amplified 5x (but so is reward)
    risk_per_trade_pct = 1.0  # 1% risk per trade
    portfolio_return = total_r * risk_per_trade_pct * leverage
    
    # Annualize
    if trades:
        first_ts = trades[0]["entry_ts"]
        last_ts = trades[-1]["exit_ts"] if trades[-1].get("exit_ts") else trades[-1]["entry_ts"]
        years = (last_ts - first_ts) / (365.25 * 24 * 3600 * 1000)
        ann_return = portfolio_return / years if years > 0 else 0
    else:
        years = 0
        ann_return = 0
    
    # Max portfolio drawdown at this leverage
    max_dd_pct = max_dd_r * risk_per_trade_pct * leverage
    
    return {
        "total_trades": len(trades),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wr, 1),
        "total_r": round(total_r, 2),
        "max_dd_r": round(max_dd_r, 2),
        "leverage": leverage,
        "portfolio_return_pct": round(portfolio_return, 2),
        "max_dd_pct": round(max_dd_pct, 2),
        "ann_return_pct": round(ann_return, 2),
        "years": round(years, 2),
        "total_bars_in_trades": total_bars,
    }


async def run():
    print("=" * 70)
    print("BTC: HODL vs SWING vs FUTURES — Head to Head")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)
    
    exchange = ccxt.binance({"enableRateLimit": True})
    try:
        # Fetch max data on multiple timeframes
        df_4h = await fetch_candles(exchange, SYMBOL, "4h", 1000)
        df_1d = await fetch_candles(exchange, SYMBOL, "1d", 500)
    finally:
        await exchange.close()
    
    titan._add_indicators(df_4h)
    titan._add_indicators(df_1d)
    
    years_4h = (df_4h.iloc[-1]["ts_ms"] - df_4h.iloc[0]["ts_ms"]) / (365.25 * 24 * 3600 * 1000)
    years_1d = (df_1d.iloc[-1]["ts_ms"] - df_1d.iloc[0]["ts_ms"]) / (365.25 * 24 * 3600 * 1000)
    
    print(f"\nData: 4H={len(df_4h)} candles ({years_4h:.2f}yr), 1D={len(df_1d)} candles ({years_1d:.2f}yr)")
    
    # ================================================================
    # PART 1: HODL
    # ================================================================
    print("\n" + "=" * 70)
    print("1. HODL (Buy and Hold)")
    print("=" * 70)
    
    hodl_4h = compute_hodl_metrics(df_4h)
    hodl_1d = compute_hodl_metrics(df_1d)
    
    print(f"\n  4H period ({hodl_4h['years']}yr):")
    print(f"    {hodl_4h['start_price']:,.0f} -> {hodl_4h['end_price']:,.0f}")
    print(f"    Total return: {hodl_4h['total_return_pct']:+.2f}%")
    print(f"    Annualized:   {hodl_4h['ann_return_pct']:+.2f}%")
    print(f"    Max drawdown: {hodl_4h['max_drawdown_pct']:.2f}%")
    print(f"    % time in >10% drawdown: {hodl_4h['pct_candles_in_10pct_dd']}%")
    
    print(f"\n  1D period ({hodl_1d['years']}yr):")
    print(f"    {hodl_1d['start_price']:,.0f} -> {hodl_1d['end_price']:,.0f}")
    print(f"    Total return: {hodl_1d['total_return_pct']:+.2f}%")
    print(f"    Annualized:   {hodl_1d['ann_return_pct']:+.2f}%")
    print(f"    Max drawdown: {hodl_1d['max_drawdown_pct']:.2f}%")
    print(f"    % time in >10% drawdown: {hodl_1d['pct_candles_in_10pct_dd']}%")
    
    # ================================================================
    # PART 2: Titan Trading (various configs)
    # ================================================================
    print("\n" + "=" * 70)
    print("2. TITAN TRADING — Spot (1x leverage)")
    print("=" * 70)
    
    configs = [
        ("Default (SL=1.5, TP=adaptive)", 1.5, 0, 55),
        ("BTC-optimized (SL=1.75, TP=4.0)", 1.75, 4.0, 55),
        ("High-conf (SL=1.75, TP=4.0, MC=70)", 1.75, 4.0, 70),
        ("Tight (SL=1.0, TP=1.5, MC=65)", 1.0, 1.5, 65),
    ]
    
    all_trades_by_config = {}
    
    for label, sl, tp, mc in configs:
        trades = run_titan_trades(df_4h, sl_mult=sl, tp_mult=tp, min_conf=mc)
        all_trades_by_config[label] = trades
        
        # Show at different leverages
        print(f"\n  --- {label} ---")
        for lev in [1, 3, 5, 10]:
            m = compute_trading_metrics(trades, leverage=lev)
            if not m:
                print(f"    {lev}x: No trades")
                continue
            print(f"    {lev}x: Return={m['portfolio_return_pct']:+.1f}% | MaxDD={m['max_dd_pct']:.1f}% | "
                  f"Trades={m['total_trades']} | WR={m['win_rate']}% | TotalR={m['total_r']:+.1f}")
    
    # ================================================================
    # PART 3: Direct comparison
    # ================================================================
    print("\n" + "=" * 70)
    print("3. DIRECT COMPARISON (same 4H period)")
    print("=" * 70)
    
    hodl_ret = hodl_4h["ann_return_pct"]
    hodl_dd = hodl_4h["max_drawdown_pct"]
    
    print(f"\n  HODL:")
    print(f"    Ann. Return: {hodl_ret:+.1f}% | Max DD: {hodl_dd:.1f}% | Effort: zero")
    print(f"    Return/DD ratio: {hodl_ret/hodl_dd:.2f}")
    
    print(f"\n  Trading (BTC-optimized, SL=1.75, TP=4.0, MC=55):")
    trades = all_trades_by_config["BTC-optimized (SL=1.75, TP=4.0)"]
    for lev in [1, 3, 5]:
        m = compute_trading_metrics(trades, leverage=lev)
        if not m:
            continue
        ret = m["portfolio_return_pct"]
        dd = m["max_dd_pct"]
        ret_dd = ret / dd if dd > 0 else 0
        print(f"    {lev}x: Ann. Return={ret:+.1f}% | Max DD={dd:.1f}% | Return/DD={ret_dd:.2f} | "
              f"Trades={m['total_trades']}")
    
    # ================================================================
    # PART 4: Risk-adjusted comparison
    # ================================================================
    print("\n" + "=" * 70)
    print("4. RISK-ADJUSTED SCORE (Return / MaxDD — higher is better)")
    print("=" * 70)
    
    scores = []
    scores.append(("HODL", hodl_ret, hodl_dd, hodl_ret / hodl_dd if hodl_dd > 0 else 0))
    
    for label, sl, tp, mc in configs:
        trades = all_trades_by_config[label]
        for lev in [1, 3, 5]:
            m = compute_trading_metrics(trades, leverage=lev)
            if not m or m["max_dd_pct"] == 0:
                continue
            ret = m["ann_return_pct"]
            dd = m["max_dd_pct"]
            scores.append((f"{label} @{lev}x", ret, dd, ret / dd))
    
    scores.sort(key=lambda x: x[3], reverse=True)
    
    print(f"\n  {'Rank':>4} {'Strategy':45s} {'Ann.Ret':>8} {'MaxDD':>7} {'Score':>7}")
    print("  " + "-" * 75)
    for i, (name, ret, dd, score) in enumerate(scores):
        print(f"  {i+1:>4} {name:45s} {ret:>+7.1f}% {dd:>6.1f}% {score:>7.2f}")
    
    # ================================================================
    # PART 5: The verdict
    # ================================================================
    print("\n" + "=" * 70)
    print("5. VERDICT")
    print("=" * 70)
    
    best_hodl_score = hodl_ret / hodl_dd if hodl_dd > 0 else 0
    best_trade = max(scores[1:], key=lambda x: x[3]) if len(scores) > 1 else None
    
    print(f"""
  HODL:
    + Simple, zero effort
    + Captures full bull run
    - Experiences full drawdowns ({hodl_dd:.0f}% at worst)
    - No profit in bear markets
    - No risk management

  TRADING (Titan, BTC-optimized):
    + Defined risk per trade (you know max loss upfront)
    + Can go SHORT in bear markets
    + Better sleep at night (max DD = {best_trade[2]:.0f}% vs {hodl_dd:.0f}%)
    - Requires attention, execution, discipline
    - Misses some upside while in cash between signals
    - Fees and slippage eat into returns

  Risk-adjusted winner: {'HODL' if best_hodl_score > best_trade[3] else 'TRADING'} ({max(best_hodl_score, best_trade[3]):.2f} vs {min(best_hodl_score, best_trade[3]):.2f})
""")
    
    # Save results
    output = {
        "hodl_4h": hodl_4h,
        "hodl_1d": hodl_1d,
        "trading_configs": {
            label: compute_trading_metrics(trades, leverage=5)
            for label, trades in all_trades_by_config.items()
        },
        "risk_adjusted_ranking": [{"name": s[0], "ann_return": s[1], "max_dd": s[2], "score": s[3]} for s in scores],
    }
    with open("/tmp/btc_hodl_vs_trade.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    print("  Results saved to /tmp/btc_hodl_vs_trade.json")


if __name__ == "__main__":
    asyncio.run(run())
