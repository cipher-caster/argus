"""
Backtest Engine — reusable core for Oracle + Titan signal simulation.

Extracted from run_signal_backtest.py so that optimize_trading.py and
other scripts can call it programmatically without subprocess overhead.

Public API:
    BacktestConfig      — dataclass of all knobs
    compute_stats()     — summarise a list of signal dicts
    load_candles()      — async, returns DataFrame
    load_and_prepare_data() — load + add indicators for all symbols at once
    build_macro_biases()
    get_macro_bias()
    resolve_outcome()
    derive_market_state()
    backtest_symbol()   — walk-forward simulation for one coin
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional

import pandas as pd
from sqlmodel import select

from app.storage import Database
from app.schemas.candle import Candle as DbCandle
from app.strategies.oracle import OracleStrategy
from app.strategies.titan import TitanStrategy, calculate_risk_levels

oracle = OracleStrategy()
titan = TitanStrategy()

WARMUP = 200
DEFAULT_COINS = ["BTC", "ETH", "BNB", "TRX", "XRP", "FET", "NEAR", "ARB", "ATOM", "DOGE", "APT"]


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class BacktestConfig:
    symbols: list[str] = field(default_factory=lambda: list(DEFAULT_COINS))
    provider: str = "okx"    # which exchange's candle data to use
    sl_mult: float = 1.5
    tp_mult: float = 2.0
    tp_adaptive: bool = False
    min_titan_confidence: int = 55
    block_sleeping: bool = True
    block_volatile: bool = True
    macro_guard: bool = True     # soft macro guard
    strict_macro: bool = False   # strict macro (overrides macro_guard if True)
    max_hold_candles: int = 42

    @property
    def name(self) -> str:
        """Human-readable identifier for this config."""
        tp_str = "adaptive" if self.tp_adaptive and self.tp_mult == 0 else f"tp{self.tp_mult}"
        flags = []
        if self.block_sleeping:
            flags.append("no_sleep")
        if self.strict_macro:
            flags.append("strict_macro")
        elif self.macro_guard:
            flags.append("soft_macro")
        flag_str = "_".join(flags)
        return f"sl{self.sl_mult}_{tp_str}_conf{self.min_titan_confidence}{'_' + flag_str if flag_str else ''}"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

async def load_candles(symbol: str, timeframe: str, provider: str = "okx") -> pd.DataFrame:
    """Load candles from DB (filtered by provider) and return as DataFrame."""
    async with Database.get_session() as session:
        stmt = (
            select(DbCandle)
            .where(
                DbCandle.symbol == symbol,
                DbCandle.timeframe == timeframe,
                DbCandle.provider == provider,
            )
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


async def load_and_prepare_data(symbols: list[str], provider: str = "okx") -> dict:
    """
    Load all candle data and pre-compute BTC indicators in one shot.
    Returns a bundle dict:
        {
          "btc_4h": DataFrame,       # BTC 4H with indicators already added
          "btc_1d": DataFrame,       # BTC 1D with indicators
          "btc_macro_biases": dict,
          "coin_data": {
              "BTC": {"4h": DataFrame, "1d": DataFrame},
              "ETH": {"4h": DataFrame, "1d": DataFrame},
              ...
          }
        }
    Candle data is shared: BTC DataFrames appear both as btc_4h/btc_1d AND
    inside coin_data["BTC"] to avoid duplication.
    """
    print("Loading BTC candles...")
    btc_4h = await load_candles("BTC/USDT", "4h", provider)
    btc_1d = await load_candles("BTC/USDT", "1d", provider)

    if btc_4h.empty or len(btc_4h) < WARMUP + 10:
        raise ValueError(f"Not enough BTC 4H data (have {len(btc_4h)}, need >{WARMUP})")

    print(f"  BTC: {len(btc_4h)} × 4H, {len(btc_1d)} × 1D")
    print("Pre-computing BTC indicators...")
    oracle._add_indicators(btc_4h)
    oracle._add_indicators(btc_1d)
    titan._add_indicators(btc_4h)
    btc_macro_biases = build_macro_biases(btc_1d)

    coin_data: dict[str, dict] = {"BTC": {"4h": btc_4h, "1d": btc_1d}}

    for coin in symbols:
        if coin == "BTC":
            continue
        sym_4h = f"{coin}/USDT"
        sym_1d = f"{coin}/USDT"
        df_4h = await load_candles(sym_4h, "4h", provider)
        df_1d = await load_candles(sym_1d, "1d", provider)
        print(f"  {coin}: {len(df_4h)} × 4H, {len(df_1d)} × 1D")
        coin_data[coin] = {"4h": df_4h, "1d": df_1d}

    return {
        "btc_4h": btc_4h,
        "btc_1d": btc_1d,
        "btc_macro_biases": btc_macro_biases,
        "coin_data": coin_data,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def resolve_outcome(
    df_4h: pd.DataFrame,
    entry_idx: int,
    direction: str,
    tp: float,
    sl: float,
    max_hold: int = 42,
) -> tuple:
    """
    Scan forward up to max_hold candles to find WIN/LOSS/REVIEW.
    Conservative: same-candle TP+SL hit → LOSS.
    Returns (outcome, resolved_price, resolved_ts_ms).
    """
    for j in range(entry_idx + 1, min(entry_idx + 1 + max_hold, len(df_4h))):
        candle = df_4h.iloc[j]
        h, l = candle["high"], candle["low"]

        if direction == "LONG":
            sl_hit = l <= sl
            tp_hit = h >= tp
        else:
            sl_hit = h >= sl
            tp_hit = l <= tp

        if sl_hit and tp_hit:
            return "LOSS", float(sl), int(candle["ts_ms"])
        if sl_hit:
            return "LOSS", float(sl), int(candle["ts_ms"])
        if tp_hit:
            return "WIN", float(tp), int(candle["ts_ms"])

    return "REVIEW", None, None


async def resolve_outcome_with_tiebreaker(
    df_4h: pd.DataFrame,
    entry_idx: int,
    direction: str,
    tp: float,
    sl: float,
    symbol: str,
    max_hold: int = 42,
) -> tuple:
    """
    Like resolve_outcome but uses 5min candles to break same-candle TP+SL ties.
    Falls back to conservative LOSS if 5min data is unavailable.
    Returns (outcome, resolved_price, resolved_ts_ms).
    """
    for j in range(entry_idx + 1, min(entry_idx + 1 + max_hold, len(df_4h))):
        candle = df_4h.iloc[j]
        h, l = candle["high"], candle["low"]
        c_ts_ms = int(candle["ts_ms"])

        if direction == "LONG":
            sl_hit = l <= sl
            tp_hit = h >= tp
        else:
            sl_hit = h >= sl
            tp_hit = l <= tp

        if sl_hit and tp_hit:
            # Both hit in same 4H candle — fetch 5min to determine order
            tiebreak = await _tiebreaker_5m_from_db(
                symbol, direction, tp, sl, c_ts_ms,
            )
            return tiebreak["outcome"], tiebreak["resolved_price"], tiebreak["resolved_at_ms"]

        if sl_hit:
            return "LOSS", float(sl), c_ts_ms
        if tp_hit:
            return "WIN", float(tp), c_ts_ms

    return "REVIEW", None, None


async def _tiebreaker_5m_from_db(
    symbol: str,
    direction: str,
    tp: float,
    sl: float,
    candle_open_ms: int,
) -> dict:
    """
    Load 5min candles from DB for the given 4H window and walk them
    to determine which level (TP or SL) was hit first.
    Falls back to LOSS (conservative) if 5min data is unavailable.
    """
    candle_close_ms = candle_open_ms + 4 * 60 * 60 * 1000

    try:
        df_5m = await load_candles(symbol, "5m")
        if df_5m.empty:
            return {"outcome": "LOSS", "resolved_price": sl, "resolved_at_ms": candle_open_ms}

        start_ts = pd.Timestamp(candle_open_ms, unit="ms", tz="UTC")
        end_ts = pd.Timestamp(candle_close_ms, unit="ms", tz="UTC")
        mask = (df_5m["timestamp"] >= start_ts) & (df_5m["timestamp"] <= end_ts)
        candles_5m = df_5m[mask].sort_values("timestamp")

        if candles_5m.empty:
            return {"outcome": "LOSS", "resolved_price": sl, "resolved_at_ms": candle_open_ms}

        for _, c in candles_5m.iterrows():
            c_high = float(c["high"])
            c_low = float(c["low"])
            c_time = int(c["ts_ms"])

            if direction == "LONG":
                sl_first = c_low <= sl
                tp_first = c_high >= tp
            else:
                sl_first = c_high >= sl
                tp_first = c_low <= tp

            if sl_first and tp_first:
                continue  # ambiguous in same 5m candle — check next
            if sl_first:
                return {"outcome": "LOSS", "resolved_price": sl, "resolved_at_ms": c_time}
            if tp_first:
                return {"outcome": "WIN", "resolved_price": tp, "resolved_at_ms": c_time}

    except Exception:
        pass

    return {"outcome": "LOSS", "resolved_price": sl, "resolved_at_ms": candle_open_ms}


def derive_market_state(row: pd.Series) -> str:
    """Derive market state from pre-computed indicators on a 4H row."""
    state = oracle._detect_market_state(row)
    return state.get("state", "UNKNOWN")


# ---------------------------------------------------------------------------
# Core backtest per symbol
# ---------------------------------------------------------------------------

async def backtest_symbol(
    symbol: str,
    df_4h: pd.DataFrame,
    df_1d: pd.DataFrame,
    btc_4h: pd.DataFrame,
    btc_macro_biases: dict,
    config: BacktestConfig,
) -> list:
    """Walk-forward simulation for one coin. Returns list of signal dicts."""

    if df_4h.empty or df_1d.empty:
        print(f"  [{symbol}] Skipping — no candle data")
        return []

    print(f"\n  [{symbol}] Simulating {len(df_4h)} × 4H candles...")

    # Pre-compute indicators (idempotent — skip if already done)
    if "rsi" not in df_4h.columns:
        oracle._add_indicators(df_4h)
        titan._add_indicators(df_4h)
    if "rsi" not in df_1d.columns:
        oracle._add_indicators(df_1d)

    macro_biases = build_macro_biases(df_1d)
    btc_ts_index = {row["timestamp"]: i for i, (_, row) in enumerate(btc_4h.iterrows())}

    signals = []
    active_signal = None

    blocked_states = {"VOLATILE"} if config.block_volatile else set()
    if config.block_sleeping:
        blocked_states.add("SLEEPING")

    for i in range(WARMUP, len(df_4h)):
        row = df_4h.iloc[i]
        ts = row["timestamp"]
        price = float(row["close"])

        if pd.isna(row.get("rsi")) or pd.isna(row.get("ema200")):
            continue

        # --- BTC market gate ---
        btc_idx = btc_ts_index.get(ts)
        if btc_idx is None or btc_idx < WARMUP:
            continue
        btc_row = btc_4h.iloc[btc_idx]
        if pd.isna(btc_row.get("adx")):
            continue
        btc_state = derive_market_state(btc_row)
        if btc_state in blocked_states:
            continue

        btc_e = oracle._calculate_earnest_score(btc_row)
        btc_macro = get_macro_bias(ts, btc_macro_biases)
        btc_signal = oracle._synthesize_signal(btc_e["score"], btc_macro["score"])
        if btc_signal in ("SELL", "STRONG_SELL"):
            continue

        # --- Oracle signal ---
        e_result = oracle._calculate_earnest_score(row)
        e_score = e_result["score"]
        m_bias = get_macro_bias(ts, macro_biases)
        o_signal = oracle._synthesize_signal(e_score, m_bias["score"])

        if o_signal not in ("STRONG_BUY", "BUY", "STRONG_SELL", "SELL"):
            active_signal = None
            continue

        # Macro guard
        if config.strict_macro:
            if o_signal in ("BUY", "STRONG_BUY") and m_bias["bias"] != "BULLISH":
                continue
            if o_signal in ("SELL", "STRONG_SELL") and m_bias["bias"] != "BEARISH":
                continue
        elif config.macro_guard:
            if o_signal in ("BUY", "STRONG_BUY") and m_bias["bias"] == "BEARISH":
                continue
            if o_signal in ("SELL", "STRONG_SELL") and m_bias["bias"] == "BULLISH":
                continue

        # --- Titan signal ---
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

        is_long = t_signal in ("BUY", "BUY_LIMIT", "STRONG_BUY") and "BUY" in o_signal
        is_short = t_signal in ("SELL", "SELL_LIMIT", "STRONG_SELL") and "SELL" in o_signal

        if not (is_long or is_short) or t_confidence < config.min_titan_confidence:
            continue

        direction = "LONG" if is_long else "SHORT"

        if active_signal and active_signal["direction"] == direction:
            continue

        # --- Compute targets via shared calculator ---
        atr = float(row.get("atr", 0))
        if atr <= 0:
            continue

        # Resolve effective TP multiplier (preserve adaptive path for optimization)
        if config.tp_mult > 0:
            effective_tp_mult = config.tp_mult
        elif config.tp_adaptive:
            effective_tp_mult = 3.0 if btc_state == "SUPER TREND" else 2.0
        else:
            effective_tp_mult = 2.0

        targets = calculate_risk_levels(
            row=row,
            signal_type=t_signal,
            entry_price=price,
            symbol=symbol,
            sl_mult=config.sl_mult,
            tp_mult=effective_tp_mult,
        )

        sl = round(targets["sl"], 6)
        tp = round(targets["tp"], 6)
        entry = round(targets["entry"], 6)
        if tp == 0 or sl == 0:
            continue

        # --- Conviction (mirrors live signal_log formula for consistency) ---
        # All backtest signals pass the btc_state regime gate, so regime_bonus always applies.
        base_pts = (t_confidence / 100) * 60
        regime_bonus = 20
        signal_bonus = 10 if t_signal in ("BUY", "SELL", "STRONG_BUY", "STRONG_SELL") else 0
        conviction = int(min(100, base_pts + regime_bonus + signal_bonus))

        # --- Resolve outcome ---
        outcome, resolved_price, resolved_ts_ms = await resolve_outcome_with_tiebreaker(
            df_4h, i, direction, tp, sl, symbol, config.max_hold_candles,
        )

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
            provider=config.provider,
            outcome=outcome,
            resolved_at=resolved_ts_ms,
            resolved_price=resolved_price,
        )
        signals.append(signal)
        active_signal = signal

    return signals


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def compute_stats(signals: list) -> dict:
    """
    Summarise a list of signal dicts.
    Returns:
        total, wins, losses, reviews, win_rate,
        total_r, ev_per_trade, avg_rr, coin_results
    """
    if not signals:
        return {
            "total": 0, "wins": 0, "losses": 0, "reviews": 0,
            "win_rate": None, "total_r": 0.0,
            "ev_per_trade": None, "avg_rr": None,
            "coin_results": {},
        }

    wins = sum(1 for s in signals if s["outcome"] == "WIN")
    losses = sum(1 for s in signals if s["outcome"] == "LOSS")
    reviews = sum(1 for s in signals if s["outcome"] == "REVIEW")
    closed = wins + losses
    win_rate = round(wins / closed * 100, 2) if closed > 0 else None

    total_r = 0.0
    rr_sum = 0.0
    for s in signals:
        risk = abs(s["entry"] - s["sl"])
        reward = abs(s["tp"] - s["entry"])
        rr = reward / risk if risk > 0 else 0
        rr_sum += rr
        if s["outcome"] == "WIN":
            total_r += rr
        elif s["outcome"] == "LOSS":
            total_r -= 1.0

    avg_rr = round(rr_sum / len(signals), 3) if signals else None
    ev_per_trade = round(total_r / closed, 3) if closed > 0 else None

    # Per-coin breakdown
    by_symbol: dict[str, list] = defaultdict(list)
    for s in signals:
        by_symbol[s["symbol"]].append(s)

    coin_results = {}
    for sym, sigs in by_symbol.items():
        sw = sum(1 for s in sigs if s["outcome"] == "WIN")
        sl = sum(1 for s in sigs if s["outcome"] == "LOSS")
        sr = sum(1 for s in sigs if s["outcome"] == "REVIEW")
        sc = sw + sl
        sym_r = 0.0
        for s in sigs:
            risk = abs(s["entry"] - s["sl"])
            reward = abs(s["tp"] - s["entry"])
            rr = reward / risk if risk > 0 else 0
            if s["outcome"] == "WIN":
                sym_r += rr
            elif s["outcome"] == "LOSS":
                sym_r -= 1.0
        coin_results[sym] = {
            "total": len(sigs),
            "wins": sw,
            "losses": sl,
            "reviews": sr,
            "win_rate": round(sw / sc * 100, 1) if sc > 0 else None,
            "profit_r": round(sym_r, 2),
        }

    return {
        "total": len(signals),
        "wins": wins,
        "losses": losses,
        "reviews": reviews,
        "win_rate": win_rate,
        "total_r": round(total_r, 2),
        "ev_per_trade": ev_per_trade,
        "avg_rr": avg_rr,
        "coin_results": coin_results,
    }
