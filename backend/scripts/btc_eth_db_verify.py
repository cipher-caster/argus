"""
BTC + ETH Verification — DB Data, 4H + 1D only (fast).
"""
import asyncio, sys, json
from datetime import datetime, timezone
from itertools import product
import pandas as pd
import numpy as np

sys.path.insert(0, "/app")
from app.trading.backtest_engine import load_candles
from app.strategies.titan import TitanStrategy

titan = TitanStrategy()
WARMUP = 200

def backtest(df, sl=1.5, tp=0, mc=55):
    if df.empty or len(df) < WARMUP+10: return None
    trades, active = [], None
    for i in range(WARMUP, len(df)):
        row = df.iloc[i]; price = float(row["close"])
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
        mom=titan._analyze_momentum(row); vol=titan._analyze_volatility(df.iloc[max(0, i - titan.squeeze_lookback + 1) : i + 1])
        rw=df.iloc[max(0,i-4):i+1]
        bs=rw[rw["sweep_type"]=="bullish"]; rs="bullish" if not bs.empty else ("bearish" if not rw[rw["sweep_type"]=="bearish"].empty else None)
        t=titan._generate_signal(trend,mom,vol,row,rs); sig,conf=t["type"],t["confidence"]
        il=sig in ("BUY","BUY_LIMIT"); is_=sig in ("SELL","SELL_LIMIT")
        if not(il or is_) or conf<mc: continue
        if active and active["t"]==("LONG" if il else "SHORT"): continue
        a=float(row.get("atr",0)) or 0
        if a<=0: continue
        adx_val=row.get("adx")
        tm=tp if tp>0 else (3.0 if(adx_val is not None and not pd.isna(adx_val) and adx_val>40) else 2.0)
        if il: sl_=price-a*sl; tp_=price+a*tm; d="LONG"
        else: sl_=price+a*sl; tp_=price-a*tm; d="SHORT"
        active={"t":d,"e":price,"sl":sl_,"tp":tp_}
    n=len(trades); w=sum(1 for t in trades if t["r"]=="WIN"); l_=n-w
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
    ln=len([t for t in trades if t["t"]=="LONG"])
    sn=len([t for t in trades if t["t"]=="SHORT"])
    return {"n":n,"w":w,"l":l_,"wr":round(wr,1),"r":round(tr,2),"ev":round(ev,3),"mdd":round(mdd,2),"pf":round(w/max(l_,1),2),"ln":ln,"sn":sn}

def hodl(df):
    s=float(df.iloc[0]["close"]); e=float(df.iloc[-1]["close"]); ret=(e-s)/s
    pk=df["close"].expanding().max(); dd=abs(((df["close"]-pk)/pk).min())
    y=(df.iloc[-1]["ts_ms"]-df.iloc[0]["ts_ms"])/(365.25*24*3600*1000)
    ann=(1+ret)**(1/y)-1 if y>0 else 0
    return {"s":s,"e":e,"ret":round(ret*100,2),"ann":round(ann*100,2),"dd":round(dd*100,2),"y":round(y,2)}

async def run():
    print("="*70)
    print("BTC + ETH — DB Verification (4H + 1D)")
    print("="*70)

    btc_4h=await load_candles("BTC/USDT","4h")
    btc_1d=await load_candles("BTC/USDT","1d")
    eth_4h=await load_candles("ETH/USDT","4h")
    eth_1d=await load_candles("ETH/USDT","1d")

    # Cap at 1500 candles for speed (still ~0.7yr for 4H)
    MAX = 1500
    if len(btc_4h) > MAX: btc_4h = btc_4h.iloc[-MAX:].reset_index(drop=True)
    if len(btc_1d) > MAX: btc_1d = btc_1d.iloc[-MAX:].reset_index(drop=True)
    if len(eth_4h) > MAX: eth_4h = eth_4h.iloc[-MAX:].reset_index(drop=True)
    if len(eth_1d) > MAX: eth_1d = eth_1d.iloc[-MAX:].reset_index(drop=True)

    def y(df): return (df.iloc[-1]["ts_ms"]-df.iloc[0]["ts_ms"])/(365.25*24*3600*1000)

    print(f"\n  BTC 4H: {len(btc_4h)} candles ({y(btc_4h):.2f}yr)")
    print(f"  BTC 1D: {len(btc_1d)} candles ({y(btc_1d):.2f}yr)")
    print(f"  ETH 4H: {len(eth_4h)} candles ({y(eth_4h):.2f}yr)")
    print(f"  ETH 1D: {len(eth_1d)} candles ({y(eth_1d):.2f}yr)")

    for df in [btc_4h,btc_1d,eth_4h,eth_1d]:
        titan._add_indicators(df)

    # BTC
    print("\n"+"="*70)
    print("BTC 4H")
    print("="*70)
    yb=y(btc_4h)
    for lbl,sl,tp in [("Default (1.5 adapt)",1.5,0),("BTC-opt (1.75 TP=4)",1.75,4.0),("Tight (1.0 TP=1.5)",1.0,1.5),("Wide (2.0 TP=3.0)",2.0,3.0)]:
        r=backtest(btc_4h,sl,tp,55)
        if not r: continue
        ann=r["r"]/yb if yb>0 else 0
        print(f"  {lbl:25s}: {r['n']:>4} trades WR={r['wr']}% EV={r['ev']:+.3f}R R={r['r']:+.2f} Ann={ann:+.1f} MDD={r['mdd']}R PF={r['pf']} L={r['ln']} S={r['sn']}")

    print(f"\n  Sweep (by EV):")
    sls=[1.0,1.25,1.5,1.75,2.0,2.5]; tps=[0,1.5,2.0,2.5,3.0,4.0]
    sw=[]
    for sl,tp in product(sls,tps):
        r=backtest(btc_4h,sl,tp,55)
        if r and r["n"]>=10: ann=r["r"]/yb if yb>0 else 0; sw.append({"sl":sl,"tp":tp if tp>0 else "ad","ann":round(ann,2),**r})
    sw.sort(key=lambda x:x["ev"],reverse=True)
    print(f"  {'#':>3} {'SL':>5} {'TP':>4} {'N':>5} {'WR':>5} {'EV':>7} {'R':>7} {'Ann':>7} {'MDD':>5}")
    for i,r in enumerate(sw[:10]):
        tp=str(r["tp"])
        print(f"  {i+1:>3} {r['sl']:>5.2f} {tp:>4} {r['n']:>5} {r['wr']:>5}% {r['ev']:>+7.3f} {r['r']:>+7.2f} {r['ann']:>+7.2f} {r['mdd']:>5.1f}")

    h=hodl(btc_4h)
    print(f"\n  HODL: {h['s']:,.0f}->{h['e']:,.0f} = {h['ret']:+.1f}% (ann {h['ann']:+.1f}%) DD={h['dd']}%")

    # BTC 1D
    print("\n"+"="*70)
    print("BTC 1D")
    print("="*70)
    yb1=y(btc_1d)
    for lbl,sl,tp in [("Default (1.5 adapt)",1.5,0),("BTC-opt (1.75 TP=4)",1.75,4.0)]:
        r=backtest(btc_1d,sl,tp,55)
        if not r: continue
        ann=r["r"]/yb1 if yb1>0 else 0
        print(f"  {lbl:25s}: {r['n']:>4} trades WR={r['wr']}% EV={r['ev']:+.3f}R R={r['r']:+.2f} Ann={ann:+.1f} MDD={r['mdd']}R")

    # ETH
    print("\n"+"="*70)
    print("ETH 4H")
    print("="*70)
    ye=y(eth_4h)
    for lbl,sl,tp in [("Default (1.5 adapt)",1.5,0),("Wider (1.75 TP=3.0)",1.75,3.0),("Tight (1.0 TP=1.5)",1.0,1.5),("Wide (2.0 TP=4.0)",2.0,4.0)]:
        r=backtest(eth_4h,sl,tp,55)
        if not r: continue
        ann=r["r"]/ye if ye>0 else 0
        print(f"  {lbl:25s}: {r['n']:>4} trades WR={r['wr']}% EV={r['ev']:+.3f}R R={r['r']:+.2f} Ann={ann:+.1f} MDD={r['mdd']}R PF={r['pf']} L={r['ln']} S={r['sn']}")

    print(f"\n  Sweep (by EV):")
    sw2=[]
    for sl,tp in product(sls,tps):
        r=backtest(eth_4h,sl,tp,55)
        if r and r["n"]>=10: ann=r["r"]/ye if ye>0 else 0; sw2.append({"sl":sl,"tp":tp if tp>0 else "ad","ann":round(ann,2),**r})
    sw2.sort(key=lambda x:x["ev"],reverse=True)
    print(f"  {'#':>3} {'SL':>5} {'TP':>4} {'N':>5} {'WR':>5} {'EV':>7} {'R':>7} {'Ann':>7} {'MDD':>5}")
    for i,r in enumerate(sw2[:10]):
        tp=str(r["tp"])
        print(f"  {i+1:>3} {r['sl']:>5.2f} {tp:>4} {r['n']:>5} {r['wr']:>5}% {r['ev']:>+7.3f} {r['r']:>+7.2f} {r['ann']:>+7.2f} {r['mdd']:>5.1f}")

    h=hodl(eth_4h)
    print(f"\n  HODL: {h['s']:,.0f}->{h['e']:,.0f} = {h['ret']:+.1f}% (ann {h['ann']:+.1f}%) DD={h['dd']}%")

    # ETH 1D
    print("\n"+"="*70)
    print("ETH 1D")
    print("="*70)
    ye1=y(eth_1d)
    for lbl,sl,tp in [("Default (1.5 adapt)",1.5,0),("Wider (1.75 TP=3.0)",1.75,3.0)]:
        r=backtest(eth_1d,sl,tp,55)
        if not r: continue
        ann=r["r"]/ye1 if ye1>0 else 0
        print(f"  {lbl:25s}: {r['n']:>4} trades WR={r['wr']}% EV={r['ev']:+.3f}R R={r['r']:+.2f} Ann={ann:+.1f} MDD={r['mdd']}R")

if __name__=="__main__":
    asyncio.run(run())
