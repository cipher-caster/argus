"""
Signal Log Worker Jobs
======================
log_watchlist_setups   — every 5 min — fire-and-log for BTC/ETH/BNB
resolve_signal_outcomes — every hour  — WIN / LOSS / REVIEW resolution

SOL removed from watchlist (2026-03-17): backtested across 7+ parameter
combinations — consistently negative. Trend-following strategy doesn't
fit SOL's mean-reverting character on 4H.
"""
import logging
import time
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.storage import RedisClient, Database
from app.schemas.signal_log import SignalLog

logger = logging.getLogger(__name__)

# Defaults (overridable via Redis config)
DEFAULT_WATCHLIST = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT",
    "TRXUSDT", "XRPUSDT", "FETUSDT", "NEARUSDT",
    "ARBUSDT", "ATOMUSDT", "DOGEUSDT", "APTUSDT",
]
DEFAULT_MIN_TITAN_CONFIDENCE = 55
DEFAULT_REVIEW_DAYS = 7

SIGNAL_LOG_CONFIG_KEY = "signal_log:config"


async def _get_config() -> dict:
    """Read signal log config from Redis, falling back to defaults."""
    data = await RedisClient.get_json(SIGNAL_LOG_CONFIG_KEY)
    if data:
        return data
    return {
        "watchlist": DEFAULT_WATCHLIST,
        "min_titan_confidence": DEFAULT_MIN_TITAN_CONFIDENCE,
        "review_days": DEFAULT_REVIEW_DAYS,
        "block_sleeping": True,
        "block_volatile": True,
        "macro_guard": True,
        "block_btc_sell": True,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_market_state() -> str:
    """Return current market_state from cached signal-summary, or empty string."""
    data = await RedisClient.get_json("analytics:signal-summary")
    if data:
        return data.get("market_state", "")
    return ""


async def _get_btc_oracle_signal() -> str:
    """Return BTC signal from cached Oracle screener, or empty string."""
    for limit in (50, 20):
        data = await RedisClient.get_json(f"analytics:screener:4h:{limit}")
        if data:
            items = data if isinstance(data, list) else data.get("data", [])
            for item in items:
                if isinstance(item, dict) and item.get("symbol") == "BTCUSDT":
                    return item.get("signal", "")
    return ""


async def _get_oracle_score(symbol: str) -> dict:
    """Return oracle screener item for a symbol, or empty dict."""
    for limit in (50, 20):
        data = await RedisClient.get_json(f"analytics:screener:4h:{limit}")
        if data:
            items = data if isinstance(data, list) else data.get("data", [])
            for item in items:
                if isinstance(item, dict) and item.get("symbol") == symbol:
                    return item
    return {}


def _passes_market_gate(market_state: str, btc_signal: str, config: dict) -> bool:
    """Return True only when market conditions are swing-tradeable."""
    blocked_states = []
    if config.get("block_sleeping", True):
        blocked_states.append("SLEEPING")
    if config.get("block_volatile", True):
        blocked_states.append("VOLATILE")
    if market_state in blocked_states:
        logger.info(f"Signal log gate: SKIP — market is {market_state}")
        return False
    if config.get("block_btc_sell", True) and btc_signal in ("SELL", "STRONG_SELL"):
        logger.info(f"Signal log gate: SKIP — BTC Oracle is {btc_signal}")
        return False
    return True


# ---------------------------------------------------------------------------
# Job A: log_watchlist_setups
# ---------------------------------------------------------------------------

async def log_watchlist_setups(ctx):
    """
    Runs every 5 minutes. For each watchlist coin:
    1. Check market gate (market_state + BTC Oracle)
    2. Run Titan + Oracle check on 4H
    3. If setup qualifies, insert OPEN row (DB deduplicates via unique constraint)
    """
    from app.routes.strategy import get_candles_df, titan, oracle

    logger.info("Job: log_watchlist_setups — checking watchlist...")

    config = await _get_config()
    market_state = await _get_market_state()
    btc_signal = await _get_btc_oracle_signal()

    if not _passes_market_gate(market_state, btc_signal, config):
        return

    now_ms = int(time.time() * 1000)
    logged = 0

    # Collect all qualified rows first
    rows_to_insert = []

    for symbol in config["watchlist"]:
        try:
            # Fetch 4H candles
            df = await get_candles_df(symbol, timeframe="4h", limit=300)
            if df is None or df.empty:
                continue

            # Run Titan (pass symbol for per-symbol risk overrides)
            t = titan.analyze(df, symbol=symbol)
            if "error" in t:
                continue

            t_signal = t.get("signal", "")
            t_confidence = t.get("confidence", 0)

            is_long = t_signal in ("BUY", "BUY_LIMIT")
            is_short = t_signal in ("SELL", "SELL_LIMIT")
            if not (is_long or is_short) or t_confidence < config["min_titan_confidence"]:
                continue

            # Get Oracle score from cache
            o = await _get_oracle_score(symbol)
            o_score = o.get("score", 0)
            o_bias = o.get("bias", "NEUTRAL")
            o_signal = o.get("signal", "NEUTRAL")

            # Oracle must agree on direction
            if is_long and o_score <= 0:
                continue
            if is_short and o_score >= 0:
                continue

            # Soft macro guard: block worst counter-trend entries
            if config.get("macro_guard", True):
                if is_long and o_bias == "BEARISH":
                    continue  # Don't LONG into bearish macro
                if is_short and o_bias == "BULLISH":
                    continue  # Don't SHORT into bullish macro

            # Compute conviction (same formula as best-setups)
            oracle_pts = (abs(o_score) / 5) * 40
            titan_pts = (t_confidence / 100) * 40
            bonus = 0
            if t_signal in ("BUY", "SELL"):
                bonus += 10
            if abs(o_score) >= 4:
                bonus += 10
            conviction = int(min(100, oracle_pts + titan_pts + bonus))

            targets = t.get("targets", {})
            price = float(df.iloc[-1]["close"])
            reasons = t.get("reasons", [])
            fired_reason = f"Oracle {o_bias} {o_score:+d}/5 | {t_signal} {t_confidence}% | " + " | ".join(reasons[:2])

            row = dict(
                symbol=symbol,
                direction="LONG" if is_long else "SHORT",
                timeframe="4h",
                entry=round(float(targets.get("entry", price)), 6),
                tp=round(float(targets.get("tp", 0)), 6),
                sl=round(float(targets.get("sl", 0)), 6),
                conviction=conviction,
                oracle_signal=o_signal,
                titan_signal=t_signal,
                oracle_score=o_score,
                titan_confidence=int(t_confidence),
                market_state=market_state or "UNKNOWN",
                fired_reason=fired_reason,
                fired_at=now_ms,
                outcome="OPEN",
            )

            rows_to_insert.append(row)
            logged += 1
            logger.info(f"Signal log: {symbol} {row['direction']} conviction={conviction} state={market_state}")

        except Exception as e:
            logger.warning(f"log_watchlist_setups error for {symbol}: {e}")

    # Batch insert all rows in one session
    if rows_to_insert:
        async with Database.get_session() as session:
            for row in rows_to_insert:
                stmt = (
                    pg_insert(SignalLog)
                    .values(**row)
                    .on_conflict_do_nothing(
                        index_elements=["symbol", "direction"],
                        index_where=text("outcome = 'OPEN'"),
                    )
                )
                await session.execute(stmt)
            await session.commit()

    logger.info(f"Job: log_watchlist_setups complete — {logged} new signal(s) logged")


# ---------------------------------------------------------------------------
# Job B: resolve_signal_outcomes
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Job B: log_best_setups (scanner signals)
# ---------------------------------------------------------------------------

async def log_best_setups(ctx):
    """
    Reads the cached best-setups result (warmed every 5 min by sync_analytics_cache)
    and persists qualifying signals to signal_log with source='scanner'.
    This ensures signals shown in ActiveSetups/BestSetups are tracked for outcomes.
    """
    cache_key = "analytics:best-setups:4h:50"
    cached = await RedisClient.get_json(cache_key)
    if not cached:
        logger.info("Job: log_best_setups — no cached best-setups, skipping")
        return

    items = cached.get("data", [])
    if not items:
        return

    config = await _get_config()
    market_state = await _get_market_state()
    now_ms = int(time.time() * 1000)
    logged = 0

    # Collect all qualified rows first
    rows_to_insert = []

    for item in items:
        try:
            conviction = item.get("conviction", 0)
            if conviction < 60:
                continue

            symbol = item.get("symbol", "").replace("/", "")
            direction = item.get("direction", "")
            if not symbol or not direction:
                continue

            o_score = item.get("oracle_score", 0)
            o_bias = "BULLISH" if o_score > 0 else "BEARISH" if o_score < 0 else "NEUTRAL"
            t_signal = item.get("titan_signal", "")

            row = dict(
                symbol=symbol,
                direction=direction,
                timeframe="4h",
                entry=round(float(item.get("entry", 0)), 6),
                tp=round(float(item.get("tp", 0)), 6),
                sl=round(float(item.get("sl", 0)), 6),
                conviction=conviction,
                oracle_signal=f"{'STRONG_BUY' if o_score >= 4 else 'BUY'}" if o_score > 0
                    else f"{'STRONG_SELL' if o_score <= -4 else 'SELL'}",
                titan_signal=t_signal,
                oracle_score=o_score,
                titan_confidence=0,  # not in best-setups cache
                market_state=market_state or "UNKNOWN",
                fired_reason=item.get("reason", ""),
                fired_at=now_ms,
                source="scanner",
                outcome="OPEN",
            )

            rows_to_insert.append(row)
            logged += 1

        except Exception as e:
            logger.warning(f"log_best_setups error for {item.get('symbol', '?')}: {e}")

    # Batch insert all rows in one session
    if rows_to_insert:
        async with Database.get_session() as session:
            for row in rows_to_insert:
                stmt = (
                    pg_insert(SignalLog)
                    .values(**row)
                    .on_conflict_do_nothing(
                        index_elements=["symbol", "direction"],
                        index_where=text("outcome = 'OPEN'"),
                    )
                )
                await session.execute(stmt)
            await session.commit()

    if logged:
        logger.info(f"Job: log_best_setups — {logged} scanner signal(s) logged")


# ---------------------------------------------------------------------------
# Job C: resolve_signal_outcomes
# ---------------------------------------------------------------------------

async def resolve_signal_outcomes(ctx):
    """
    Runs every 30min. Resolves all OPEN signals using candle high/low data.
    Walks candles chronologically from fired_at to check TP/SL ordering.
    - WIN   — TP hit before SL
    - LOSS  — SL hit before TP
    - REVIEW — fired_at > 7 days ago, neither hit
    """
    await resolve_outcomes_historical(ctx)


# ---------------------------------------------------------------------------
# Job D: resolve_outcomes_historical
# ---------------------------------------------------------------------------

async def resolve_outcomes_historical(ctx):
    """
    Resolve OPEN signals using candle high/low data instead of current price.
    Called during startup recovery to catch TP/SL hits that occurred during downtime.

    For each OPEN signal:
    1. Fetch 4H candles from fired_at to now
    2. Walk candles chronologically
    3. Check if candle high/low crossed TP or SL
    4. If both hit in same candle, use candle direction to determine which hit first
    """
    from app.routes.strategy import get_candles_df

    logger.info("Job: resolve_outcomes_historical — checking open signals with candle data...")

    config = await _get_config()
    now_ms = int(time.time() * 1000)
    review_threshold_ms = config["review_days"] * 24 * 60 * 60 * 1000
    resolved = 0

    async with Database.get_session() as session:
        stmt = select(SignalLog).where(SignalLog.outcome == "OPEN")
        result = await session.execute(stmt)
        open_signals = result.scalars().all()

        # Fetch candles once per unique symbol
        unique_symbols = {sig.symbol for sig in open_signals}
        candle_cache = {}
        for sym in unique_symbols:
            df = await get_candles_df(sym, timeframe="4h", limit=300)
            if df is not None and not df.empty:
                candle_cache[sym] = df

        for sig in open_signals:
            try:
                # Use cached candle data for this symbol
                df = candle_cache.get(sig.symbol)
                if df is None:
                    continue

                if "timestamp" not in df.columns:
                    logger.warning(f"Historical resolve: no timestamp column for {sig.symbol}, skipping")
                    continue

                # Only look at candles at or after the signal fired, oldest first
                candles_after = df[df["timestamp"] >= sig.fired_at].sort_values("timestamp")

                if candles_after.empty:
                    # No candles after signal fired — check review timeout
                    if (now_ms - sig.fired_at) >= review_threshold_ms:
                        sig.outcome = "REVIEW"
                        sig.resolved_at = now_ms
                        session.add(sig)
                        resolved += 1
                    continue

                new_outcome = None
                resolved_at_ms = None
                resolved_price = None

                for _, candle in candles_after.iterrows():
                    c_high = float(candle.get("high", 0))
                    c_low = float(candle.get("low", 0))
                    c_open = float(candle.get("open", 0))
                    c_close = float(candle.get("close", 0))
                    c_time = int(candle.get("timestamp", 0))

                    tp_hit = False
                    sl_hit = False

                    if sig.direction == "LONG":
                        if sig.tp > 0 and c_high >= sig.tp:
                            tp_hit = True
                        if sig.sl > 0 and c_low <= sig.sl:
                            sl_hit = True
                    else:  # SHORT
                        if sig.tp > 0 and c_low <= sig.tp:
                            tp_hit = True
                        if sig.sl > 0 and c_high >= sig.sl:
                            sl_hit = True

                    if tp_hit and sl_hit:
                        # Both hit in same candle — use candle direction to infer order.
                        # LONG: bullish candle (close >= open) → dipped to SL first, then rallied → LOSS
                        #        bearish candle → rose to TP first, then dropped → WIN
                        # SHORT: bearish candle (close <= open) → rallied to SL first, then dropped → LOSS
                        #         bullish candle → fell to TP first, then rallied → WIN
                        if sig.direction == "LONG":
                            if c_close >= c_open:  # Bullish: SL hit first
                                new_outcome = "LOSS"
                                resolved_price = sig.sl
                            else:  # Bearish: TP hit first
                                new_outcome = "WIN"
                                resolved_price = sig.tp
                        else:  # SHORT
                            if c_close <= c_open:  # Bearish: SL hit first
                                new_outcome = "LOSS"
                                resolved_price = sig.sl
                            else:  # Bullish: TP hit first
                                new_outcome = "WIN"
                                resolved_price = sig.tp
                    elif tp_hit:
                        new_outcome = "WIN"
                        resolved_price = sig.tp
                    elif sl_hit:
                        new_outcome = "LOSS"
                        resolved_price = sig.sl

                    if new_outcome:
                        resolved_at_ms = c_time
                        break

                # If no TP/SL hit, check review timeout
                if not new_outcome and (now_ms - sig.fired_at) >= review_threshold_ms:
                    new_outcome = "REVIEW"
                    resolved_at_ms = now_ms
                    resolved_price = float(candles_after.iloc[-1]["close"])

                if new_outcome:
                    sig.outcome = new_outcome
                    sig.resolved_at = resolved_at_ms
                    sig.resolved_price = resolved_price
                    session.add(sig)
                    resolved += 1

                    try:
                        from app.schemas.activity_log import log_activity
                        await log_activity("OUTCOME_RESOLVED",
                                          symbol=sig.symbol,
                                          direction=sig.direction,
                                          outcome=new_outcome,
                                          resolved_price=resolved_price,
                                          method="historical_candle")
                    except Exception:
                        pass

                    logger.info(
                        f"Historical resolve: {sig.symbol} {sig.direction} → {new_outcome} "
                        f"@ {resolved_price} (entry={sig.entry} tp={sig.tp} sl={sig.sl})"
                    )

            except Exception as e:
                logger.warning(f"Historical resolve error for {sig.symbol}: {e}")

        if resolved:
            await session.commit()

    logger.info(f"Job: resolve_outcomes_historical complete — {resolved} signal(s) resolved")
