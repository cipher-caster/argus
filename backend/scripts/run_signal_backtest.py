#!/usr/bin/env python3
"""
Signal Backtest Script — Oracle + Titan on 4H
====================================================
Replays the Oracle + Titan combined setup logic over historical candles.
Writes results to signal_log (source='backtest') and prints observations.

Usage (inside Docker):
    docker compose exec backend python scripts/run_signal_backtest.py
    docker compose exec backend python scripts/run_signal_backtest.py --symbols=TAO,LINK --dry-run --fix-optimal

Flags:
    --symbols=X,Y   Comma-separated coins to test (default: BTC,ETH,BNB)
    --dry-run       Print signals without writing to DB
    --clear         Delete existing backtest rows before running
    --fix-optimal   Apply all proven optimizations (BLOCK_SLEEPING + ADAPTIVE_TP + SOFT_MACRO)

Experiment flags:
    --fix-sleeping     Block SLEEPING market state
    --fix-tp           Use adaptive TP (2× ATR normal, 3× only SUPER TREND)
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
from datetime import datetime, timezone
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlmodel import select
from app.storage import Database
from app.schemas.candle import Candle as DbCandle
from app.schemas.signal_log import SignalLog
from app.strategies.oracle import OracleStrategy
from app.strategies.titan import TitanStrategy

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_COINS = ["BTC", "ETH", "BNB", "TRX", "XRP", "FET", "NEAR", "ARB", "ATOM", "DOGE", "APT"]

def _parse_symbols():
    """Parse --symbols=TAO,LINK,BTC flag into watchlist tuples."""
    for arg in sys.argv:
        if arg.startswith("--symbols="):
            coins = [c.strip().upper() for c in arg.split("=")[1].split(",") if c.strip()]
            return [(f"{c}/USDT", f"{c}/USDT") for c in coins]
    return [(f"{c}/USDT", f"{c}/USDT") for c in DEFAULT_COINS]

WATCHLIST = _parse_symbols()

WARMUP = 200          # Candles needed before indicators are reliable
MAX_HOLD_CANDLES = 42 # 7 days on 4H — mark REVIEW if unresolved
DRY_RUN = "--dry-run" in sys.argv
CLEAR_EXISTING = "--clear" in sys.argv

# Parse numeric flags
def _parse_flag(prefix, default):
    for arg in sys.argv:
        if arg.startswith(prefix):
            return float(arg.split("=")[1])
    return default

MIN_TITAN_CONFIDENCE = int(_parse_flag("--min-conv=", 55))
SL_MULT = _parse_flag("--sl-mult=", 1.5)
TP_MULT_OVERRIDE = _parse_flag("--tp-mult=", 0)  # 0 = use adaptive default

# Experiment flags
FIX_BLOCK_SLEEPING = "--fix-sleeping" in sys.argv or "--fix-all" in sys.argv or "--fix-optimal" in sys.argv
FIX_ADAPTIVE_TP = "--fix-tp" in sys.argv or "--fix-all" in sys.argv or "--fix-optimal" in sys.argv
FIX_MACRO_ALIGN = "--fix-macro" in sys.argv or "--fix-all" in sys.argv  # strict, not in optimal
FIX_SOFT_MACRO = "--fix-soft-macro" in sys.argv or "--fix-optimal" in sys.argv

oracle = OracleStrategy()
titan = TitanStrategy()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def load_candles(symbol: str, timeframe: str) -> pd.DataFrame:
    async with Database.get_session() as session:
        stmt = (
            select(DbCandle)
            .where(DbCandle.symbol == symbol, DbCandle.timeframe == timeframe)
            .order_by(DbCandle.timestamp)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame([{
        "timestamp": pd.Timestamp(r.timestamp, unit="ms", tz="UTC"),
        "open": r.open, "high": r.high, "low": r.low,
        "close": r.close, "volume": r.volume,
        "ts_ms": r.timestamp,
    } for r in rows])
    return df


def build_macro_biases(df_1d: pd.DataFrame) -> dict:
    """Pre-compute Oracle macro bias for every 1D candle."""
    biases = {}
    for _, row in df_1d.iterrows():
        biases[row["timestamp"]] = oracle._calculate_macro_bias(row)
    return biases


def get_macro_bias(ts: pd.Timestamp, macro_biases: dict) -> dict:
    """Return the most recent macro bias at or before ts."""
    candidates = [t for t in macro_biases if t <= ts]
    if not candidates:
        return {"score": 0, "bias": "NEUTRAL"}
    return macro_biases[max(candidates)]


def resolve_outcome(df_4h: pd.DataFrame, entry_idx: int, direction: str, tp: float, sl: float) -> tuple:
    """
    Scan forward up to MAX_HOLD_CANDLES to resolve WIN/LOSS/REVIEW.
    Returns (outcome, resolved_price, resolved_ts_ms).
    Conservative: if same candle hits both, LOSS wins.
    """
    for j in range(entry_idx + 1, min(entry_idx + 1 + MAX_HOLD_CANDLES, len(df_4h))):
        candle = df_4h.iloc[j]
        h, l = candle["high"], candle["low"]

        if direction == "LONG":
            sl_hit = l <= sl
            tp_hit = h >= tp
        else:
            sl_hit = h >= sl
            tp_hit = l <= tp

        if sl_hit:
            return "LOSS", float(sl), int(candle["ts_ms"])
        if tp_hit:
            return "WIN", float(tp), int(candle["ts_ms"])

    return "REVIEW", None, None


def derive_market_state(row: pd.Series) -> str:
    """Derive market state from pre-computed indicators on the 4H row."""
    state = oracle._detect_market_state(row)
    return state.get("state", "UNKNOWN")


# ---------------------------------------------------------------------------
# Core backtest per symbol
# ---------------------------------------------------------------------------

async def backtest_symbol(
    symbol: str,
    df_4h: pd.DataFrame,
    df_1d: pd.DataFrame,
    btc_4h: pd.DataFrame,        # BTC candles for market gate
    btc_macro_biases: dict,      # BTC macro biases for gate
) -> list:

    if df_4h.empty or df_1d.empty:
        print(f"  [{symbol}] Skipping — no candle data")
        return []

    print(f"\n  [{symbol}] Pre-computing indicators on {len(df_4h)} × 4H candles...")

    # Pre-compute indicators once on the full dataset
    # Only add indicators if not already done (BTC may already have them)
    if "rsi" not in df_4h.columns:
        oracle._add_indicators(df_4h)
        titan._add_indicators(df_4h)
    if "rsi" not in df_1d.columns:
        oracle._add_indicators(df_1d)

    macro_biases = build_macro_biases(df_1d)

    # Build BTC price index for gate check (timestamp → row index)
    btc_ts_index = {row["timestamp"]: i for i, (_, row) in enumerate(btc_4h.iterrows())}

    signals = []
    active_signal = None  # Dedup: only one OPEN signal per direction

    # -----------------------------------------------------------------------
    # Walk forward
    # -----------------------------------------------------------------------
    for i in range(WARMUP, len(df_4h)):
        row = df_4h.iloc[i]
        ts = row["timestamp"]
        price = float(row["close"])

        # Skip if NaN indicators (warmup artifacts)
        if pd.isna(row.get("rsi")) or pd.isna(row.get("ema200")):
            continue

        # --- Market gate ---------------------------------------------------

        # Gate 1: derive market state from BTC 4H indicators at this candle
        btc_idx = btc_ts_index.get(ts)
        if btc_idx is None or btc_idx < WARMUP:
            continue
        btc_row = btc_4h.iloc[btc_idx]
        if pd.isna(btc_row.get("adx")):
            continue
        btc_state = derive_market_state(btc_row)
        blocked_states = {"VOLATILE"}
        if FIX_BLOCK_SLEEPING:
            blocked_states.add("SLEEPING")
        if btc_state in blocked_states:
            continue  # Skip non-trending conditions

        # Gate 2: BTC Oracle signal must not be bearish
        btc_e = oracle._calculate_earnest_score(btc_row)
        btc_macro = get_macro_bias(ts, btc_macro_biases)
        btc_signal = oracle._synthesize_signal(btc_e["score"], btc_macro["score"])
        if btc_signal in ("SELL", "STRONG_SELL"):
            continue  # OBS: BTC bearish — skip

        # --- Oracle signal -------------------------------------------------
        e_result = oracle._calculate_earnest_score(row)
        e_score = e_result["score"]
        m_bias = get_macro_bias(ts, macro_biases)
        o_signal = oracle._synthesize_signal(e_score, m_bias["score"])

        if o_signal not in ("STRONG_BUY", "BUY", "STRONG_SELL", "SELL"):
            active_signal = None  # Reset dedup on neutral
            continue

        # Fix 3: Macro guard — block counter-trend entries
        if FIX_MACRO_ALIGN:
            # Strict: require macro to confirm direction
            if o_signal in ("BUY", "STRONG_BUY") and m_bias["bias"] != "BULLISH":
                continue
            if o_signal in ("SELL", "STRONG_SELL") and m_bias["bias"] != "BEARISH":
                continue

        # Soft macro: block worst counter-trend only (NEUTRAL macro allowed)
        if FIX_SOFT_MACRO:
            if o_signal in ("BUY", "STRONG_BUY") and m_bias["bias"] == "BEARISH":
                continue  # Don't LONG into bearish macro
            if o_signal in ("SELL", "STRONG_SELL") and m_bias["bias"] == "BULLISH":
                continue  # Don't SHORT into bullish macro

        # --- Titan signal --------------------------------------------------
        ema = row.get("ema200")
        trend = "BULLISH" if not pd.isna(ema) and price > ema else "BEARISH"
        momentum = titan._analyze_momentum(row)
        volatility = titan._analyze_volatility(row)

        recent_window = df_4h.iloc[max(0, i - 4):i + 1]
        bull_sweeps = recent_window[recent_window["sweep_type"] == "bullish"]
        bear_sweeps = recent_window[recent_window["sweep_type"] == "bearish"]
        recent_sweep = "bullish" if not bull_sweeps.empty else ("bearish" if not bear_sweeps.empty else None)

        t_result = titan._generate_signal(trend, momentum, volatility, row, recent_sweep)
        t_signal = t_result["type"]
        t_confidence = t_result["confidence"]

        is_long = t_signal in ("BUY", "BUY_LIMIT") and "BUY" in o_signal
        is_short = t_signal in ("SELL", "SELL_LIMIT") and "SELL" in o_signal

        if not (is_long or is_short) or t_confidence < MIN_TITAN_CONFIDENCE:
            continue

        direction = "LONG" if is_long else "SHORT"

        # Dedup: skip if same direction already active
        if active_signal and active_signal["direction"] == direction:
            continue

        # --- Compute targets -----------------------------------------------
        atr = float(row.get("atr", 0))
        if atr <= 0:
            continue

        # Use custom SL multiplier
        if is_long:
            sl = round(price - (atr * SL_MULT), 6)
        else:
            sl = round(price + (atr * SL_MULT), 6)

        # TP: use override, adaptive, or default
        if TP_MULT_OVERRIDE > 0:
            tp_mult = TP_MULT_OVERRIDE
        elif FIX_ADAPTIVE_TP:
            tp_mult = 3.0 if btc_state == "SUPER TREND" else 2.0
        else:
            tp_mult = 3.0  # baseline default

        if is_long:
            tp = round(price + (atr * tp_mult), 6)
        else:
            tp = round(price - (atr * tp_mult), 6)

        entry = round(price, 6)

        if tp == 0 or sl == 0:
            continue

        # --- Conviction score ----------------------------------------------
        oracle_pts = (abs(e_score) / 5) * 40
        titan_pts = (t_confidence / 100) * 40
        bonus = 10 if t_signal in ("BUY", "SELL") else 0
        bonus += 10 if abs(e_score) >= 4 else 0
        conviction = int(min(100, oracle_pts + titan_pts + bonus))

        # --- Resolve outcome -----------------------------------------------
        outcome, resolved_price, resolved_ts_ms = resolve_outcome(df_4h, i, direction, tp, sl)

        # --- Record --------------------------------------------------------
        # Store symbol without slash for DB consistency with live signals
        db_symbol = symbol.replace("/", "")
        fired_reason = f"Oracle {m_bias['bias']} {e_score:+d}/5 | {t_signal} {t_confidence}%"

        signal = dict(
            symbol=db_symbol,
            direction=direction,
            timeframe="4h",
            entry=entry,
            tp=tp,
            sl=sl,
            conviction=conviction,
            oracle_signal=o_signal,
            titan_signal=t_signal,
            oracle_score=e_score,
            titan_confidence=int(t_confidence),
            market_state=btc_state,
            fired_reason=fired_reason,
            fired_at=int(row["ts_ms"]),
            source="backtest",
            outcome=outcome,
            resolved_at=resolved_ts_ms,
            resolved_price=resolved_price,
        )
        signals.append(signal)
        active_signal = signal

        date_str = ts.strftime("%Y-%m-%d %H:%M")
        print(f"    {date_str} | {direction:5s} @ {price:>10.2f} | "
              f"TP {tp:>10.2f} | SL {sl:>10.2f} | "
              f"Oracle {e_score:+d} Titan {t_confidence}% | {outcome}")

    return signals


# ---------------------------------------------------------------------------
# Observations reporter
# ---------------------------------------------------------------------------

def print_observations(all_signals: list):
    print("\n" + "=" * 70)
    print("BACKTEST OBSERVATIONS")
    print("=" * 70)

    if not all_signals:
        print("  No signals fired. Possible reasons:")
        print("  - Oracle + Titan rarely agree at conviction threshold")
        print("  - Market gate filtered out most candles")
        print("  - Insufficient warmup data")
        return

    by_symbol = defaultdict(list)
    for s in all_signals:
        by_symbol[s["symbol"]].append(s)

    total_wins = sum(1 for s in all_signals if s["outcome"] == "WIN")
    total_losses = sum(1 for s in all_signals if s["outcome"] == "LOSS")
    total_review = sum(1 for s in all_signals if s["outcome"] == "REVIEW")
    closed = total_wins + total_losses
    overall_wr = round(total_wins / closed * 100, 1) if closed > 0 else None

    # Calculate R-multiples
    total_r = 0.0
    for s in all_signals:
        if s["outcome"] == "WIN":
            risk = abs(s["entry"] - s["sl"])
            reward = abs(s["tp"] - s["entry"])
            total_r += reward / risk if risk > 0 else 0
        elif s["outcome"] == "LOSS":
            total_r -= 1.0

    avg_rr = 0.0
    if all_signals:
        for s in all_signals:
            risk = abs(s["entry"] - s["sl"])
            reward = abs(s["tp"] - s["entry"])
            if risk > 0:
                avg_rr += reward / risk
        avg_rr /= len(all_signals)

    print(f"\n  OVERALL: {len(all_signals)} signals | "
          f"{total_wins}W {total_losses}L {total_review}R | "
          f"Win Rate: {overall_wr}% (break-even = 33.3%)")
    print(f"  Total Profit: {total_r:+.1f}R | Avg RR: {avg_rr:.2f}:1")
    print(f"  Settings: SL={SL_MULT}×ATR | TP={'adaptive' if FIX_ADAPTIVE_TP else str(TP_MULT_OVERRIDE or 3.0) + '×ATR'} | MinConf={MIN_TITAN_CONFIDENCE}%")

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

    for symbol, sigs in sorted(by_symbol.items()):
        wins = sum(1 for s in sigs if s["outcome"] == "WIN")
        losses = sum(1 for s in sigs if s["outcome"] == "LOSS")
        reviews = sum(1 for s in sigs if s["outcome"] == "REVIEW")
        cl = wins + losses
        wr = round(wins / cl * 100, 1) if cl > 0 else None
        longs = [s for s in sigs if s["direction"] == "LONG"]
        shorts = [s for s in sigs if s["direction"] == "SHORT"]

        sym_r = 0.0
        for s in sigs:
            if s["outcome"] == "WIN":
                risk = abs(s["entry"] - s["sl"])
                reward = abs(s["tp"] - s["entry"])
                sym_r += reward / risk if risk > 0 else 0
            elif s["outcome"] == "LOSS":
                sym_r -= 1.0

        print(f"\n  {symbol}:")
        print(f"    Total signals : {len(sigs)} ({len(longs)} LONG, {len(shorts)} SHORT)")
        print(f"    Win/Loss/Review: {wins}/{losses}/{reviews}")
        print(f"    Win Rate       : {wr}%")
        print(f"    Profit         : {sym_r:+.1f}R")

        # Conviction breakdown
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

        # Market state breakdown
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
    coins = [w[0].replace("/USDT", "") for w in WATCHLIST]
    print("=" * 70)
    print(f"Argus Signal Backtest — {', '.join(coins)} (4H)")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'WRITE TO DB'}")
    fixes = []
    if FIX_BLOCK_SLEEPING: fixes.append("BLOCK_SLEEPING")
    if FIX_ADAPTIVE_TP: fixes.append("ADAPTIVE_TP")
    if FIX_MACRO_ALIGN: fixes.append("MACRO_ALIGN")
    if FIX_SOFT_MACRO: fixes.append("SOFT_MACRO")
    print(f"Fixes: {', '.join(fixes) if fixes else 'NONE (baseline)'}")
    print(f"SL: {SL_MULT}× ATR | TP: {'adaptive' if FIX_ADAPTIVE_TP else str(TP_MULT_OVERRIDE or 3.0) + '×'} | MinConf: {MIN_TITAN_CONFIDENCE}%")
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

    # Load all candle data
    print("\nLoading candle data...")
    btc_sym_4h, btc_sym_1d = "BTC/USDT", "BTC/USDT"
    btc_4h = await load_candles(btc_sym_4h, "4h")
    btc_1d = await load_candles(btc_sym_1d, "1d")
    print(f"  BTC: {len(btc_4h)} × 4H candles, {len(btc_1d)} × 1D candles")

    if len(btc_4h) < WARMUP + 10:
        print(f"\nERROR: Not enough BTC 4H data (need >{WARMUP}, have {len(btc_4h)})")
        return

    # Pre-compute BTC indicators (needed for market gate on ALL coins)
    print("\nPre-computing BTC indicators for market gate...")
    oracle._add_indicators(btc_4h)
    oracle._add_indicators(btc_1d)
    titan._add_indicators(btc_4h)
    btc_macro_biases = build_macro_biases(btc_1d)

    all_signals = []

    for sym_4h, sym_1d in WATCHLIST:
        df_4h = btc_4h if sym_4h == "BTC/USDT" else await load_candles(sym_4h, "4h")
        df_1d = btc_1d if sym_1d == "BTC/USDT" else await load_candles(sym_1d, "1d")
        print(f"  {sym_4h}: {len(df_4h)} × 4H, {len(df_1d)} × 1D")
        sigs = await backtest_symbol(sym_4h, df_4h, df_1d, btc_4h, btc_macro_biases)
        all_signals.extend(sigs)

    print_observations(all_signals)

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
