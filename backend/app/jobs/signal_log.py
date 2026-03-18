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

from sqlalchemy import select
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

    for symbol in config["watchlist"]:
        try:
            # Fetch 4H candles
            df = await get_candles_df(symbol, timeframe="4h", limit=300)
            if df is None or df.empty:
                continue

            # Run Titan
            t = titan.analyze(df)
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

            # DB-level dedup: unique constraint on (symbol, direction) WHERE outcome='OPEN'
            async with Database.get_session() as session:
                stmt = (
                    pg_insert(SignalLog)
                    .values(**row)
                    .on_conflict_do_nothing(index_elements=["symbol", "direction"])
                )
                await session.execute(stmt)
                await session.commit()

            logged += 1
            logger.info(f"Signal log: {symbol} {row['direction']} conviction={conviction} state={market_state}")

        except Exception as e:
            logger.warning(f"log_watchlist_setups error for {symbol}: {e}")

    logger.info(f"Job: log_watchlist_setups complete — {logged} new signal(s) logged")


# ---------------------------------------------------------------------------
# Job B: resolve_signal_outcomes
# ---------------------------------------------------------------------------

async def resolve_signal_outcomes(ctx):
    """
    Runs every hour. Resolves all OPEN signals:
    - WIN   — current price >= tp
    - LOSS  — current price <= sl
    - REVIEW — fired_at > 7 days ago, neither hit (stay visible, not auto-closed)
    """
    logger.info("Job: resolve_signal_outcomes — checking open signals...")

    config = await _get_config()

    # Get current prices from Redis
    tickers_raw = await RedisClient.get_json("market:tickers")
    if not tickers_raw:
        logger.warning("resolve_signal_outcomes: no market:tickers in Redis, skipping")
        return

    # Build symbol → price map (symbols in tickers are "BASE/USDT" format)
    prices: dict[str, float] = {}
    for t in tickers_raw:
        sym = t.get("symbol", "").replace("/", "")  # "BTC/USDT" → "BTCUSDT"
        price = t.get("price")
        if sym and price:
            prices[sym] = float(price)

    now_ms = int(time.time() * 1000)
    review_threshold_ms = config["review_days"] * 24 * 60 * 60 * 1000
    resolved = 0

    async with Database.get_session() as session:
        stmt = select(SignalLog).where(SignalLog.outcome == "OPEN")
        result = await session.execute(stmt)
        open_signals = result.scalars().all()

        for sig in open_signals:
            current_price = prices.get(sig.symbol)
            if current_price is None:
                continue

            new_outcome = None

            if sig.tp > 0 and (
                (sig.direction == "LONG" and current_price >= sig.tp) or
                (sig.direction == "SHORT" and current_price <= sig.tp)
            ):
                new_outcome = "WIN"

            elif sig.sl > 0 and (
                (sig.direction == "LONG" and current_price <= sig.sl) or
                (sig.direction == "SHORT" and current_price >= sig.sl)
            ):
                new_outcome = "LOSS"

            elif (now_ms - sig.fired_at) >= review_threshold_ms:
                new_outcome = "REVIEW"

            if new_outcome:
                sig.outcome = new_outcome
                sig.resolved_at = now_ms
                sig.resolved_price = current_price
                session.add(sig)
                resolved += 1
                logger.info(
                    f"Signal resolved: {sig.symbol} {sig.direction} → {new_outcome} "
                    f"@ {current_price} (entry={sig.entry} tp={sig.tp} sl={sig.sl})"
                )

        if resolved:
            await session.commit()

    logger.info(f"Job: resolve_signal_outcomes complete — {resolved} signal(s) resolved")
