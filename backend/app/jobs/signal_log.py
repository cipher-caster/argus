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

import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.storage import RedisClient, Database
from app.schemas.signal_log import SignalLog
from app.schemas.trading import Position, TradeEvent
from app.utils.trading_utils import calculate_conviction

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


async def _resolve_tiebreaker_5m(
    symbol: str,
    direction: str,
    tp: float,
    sl: float,
    candle_open_ms: int,
    provider=None,
) -> dict:
    """
    When both TP and SL are hit in the same 4H candle, fetch 5min candles
    for that 4H window and walk them to determine which level was hit first.

    Returns dict with outcome, resolved_price, and resolved_at_ms.
    Falls back to LOSS (conservative) if 5min data is unavailable.
    """
    from app.routes.strategy import get_candles_df

    candle_close_ms = candle_open_ms + 4 * 60 * 60 * 1000  # 4H window

    try:
        df_5m = await get_candles_df(symbol, timeframe="5m", limit=48, provider=provider)
        if df_5m is None or df_5m.empty:
            return {"outcome": "LOSS", "resolved_price": sl, "resolved_at_ms": candle_open_ms}

        # Filter to candles within the 4H window
        start_ts = pd.Timestamp(candle_open_ms, unit="ms")
        end_ts = pd.Timestamp(candle_close_ms, unit="ms")
        mask = (df_5m["timestamp"] >= start_ts) & (df_5m["timestamp"] <= end_ts)
        candles_5m = df_5m[mask].sort_values("timestamp")

        if candles_5m.empty:
            return {"outcome": "LOSS", "resolved_price": sl, "resolved_at_ms": candle_open_ms}

        for _, c in candles_5m.iterrows():
            c_high = float(c.get("high", 0))
            c_low = float(c.get("low", 0))
            c_ts = c.get("timestamp", 0)
            c_time = int(c_ts.timestamp() * 1000) if hasattr(c_ts, "timestamp") else int(c_ts)

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

    except Exception as e:
        logger.warning(f"Tiebreaker 5m fetch failed for {symbol}: {e}")

    # Conservative fallback
    return {"outcome": "LOSS", "resolved_price": sl, "resolved_at_ms": candle_open_ms}


# ---------------------------------------------------------------------------
# Job A: log_watchlist_setups
# ---------------------------------------------------------------------------

async def log_watchlist_setups(ctx):
    """
    Runs at 4H candle close. For each watchlist coin:
    1. Run Titan on 4H
    2. If signal qualifies (direction + conviction), log it
    Direction is filtered by regime: BULL → longs, BEAR → shorts
    """
    from app.routes.strategy import get_candles_df, titan
    from app.providers import get_provider

    logger.info("Job: log_watchlist_setups — checking watchlist...")

    config = await _get_config()
    now_ms = int(time.time() * 1000)
    logged = 0

    # Detect regime from BTC weekly EMA50 (cached to avoid recomputing on every watchlist scan)
    REGIME_CACHE_KEY = "market:regime"
    REGIME_CACHE_TTL = 3600  # 1 hour

    regime = "UNKNOWN"
    cached_regime = await RedisClient.get_json(REGIME_CACHE_KEY)
    if cached_regime:
        regime = cached_regime.get("regime", "UNKNOWN")
    else:
        try:
            from app.trading.backtest_engine import load_candles
            import pandas_ta as _ta
            btc_weekly = await load_candles("BTC/USDT", "1w")
            if not btc_weekly.empty and len(btc_weekly) > 50:
                btc_weekly["ema50"] = _ta.ema(btc_weekly["close"], length=50)
                last = btc_weekly.iloc[-2]  # Use last closed candle — iloc[-1] may be an incomplete open candle
                if not pd.isna(last.get("ema50")):
                    regime = "BULL" if float(last["close"]) > float(last["ema50"]) else "BEAR"
            await RedisClient.set_json(REGIME_CACHE_KEY, {"regime": regime}, ttl=REGIME_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Regime detection failed: {e}, using UNKNOWN")

    # Collect all qualified rows first
    rows_to_insert = []

    # Share one provider across all symbol fetches to avoid repeated exchangeInfo calls
    shared_provider = get_provider()
    try:
        for symbol in config["watchlist"]:
            try:
                # Fetch 4H candles
                df = await get_candles_df(symbol, timeframe="4h", limit=300, provider=shared_provider)
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

                # Regime-based direction filter: BEAR → shorts only, BULL → longs only
                regime_aligned = (regime == "BULL" and is_long) or (regime == "BEAR" and is_short)
                if regime != "UNKNOWN" and not regime_aligned:
                    logger.info(f"Signal log: SKIP {symbol} {t_signal} — counter-trend ({regime} regime)")
                    continue

                # Compute conviction (regime-based, not Oracle-based)
                conviction = calculate_conviction(
                    confidence=t_confidence,
                    regime_aligned=regime_aligned,
                    is_market_signal=t_signal in ("BUY", "SELL"),
                )

                # Regime tag for reason
                reg_tag = "trend" if regime_aligned else "counter"
                reasons = t.get("reasons", [])
                fired_reason = f"({reg_tag}) {t_signal} {t_confidence}% | " + " | ".join(reasons[:2])

                targets = t.get("targets", {})
                price = float(df.iloc[-1]["close"])

                row = dict(
                    symbol=symbol,
                    direction="LONG" if is_long else "SHORT",
                    timeframe="4h",
                    entry=round(float(targets.get("entry", price)), 6),
                    tp=round(float(targets.get("tp", 0)), 6),
                    sl=round(float(targets.get("sl", 0)), 6),
                    conviction=conviction,
                    oracle_signal="N/A",
                    titan_signal=t_signal,
                    oracle_score=0,
                    titan_confidence=int(t_confidence),
                    market_state=regime,
                    fired_reason=fired_reason,
                    fired_at=now_ms,
                    outcome="OPEN",
                )

                rows_to_insert.append(row)
                logged += 1
                logger.info(f"Signal log: {symbol} {row['direction']} conviction={conviction} regime={regime}")

            except Exception as e:
                logger.warning(f"log_watchlist_setups error for {symbol}: {e}")
    finally:
        await shared_provider.close()

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
    now_ms = int(time.time() * 1000)
    logged = 0
    rejected = 0

    # Collect all qualified rows first
    rows_to_insert = []

    for item in items:
        try:
            symbol = item.get("symbol", "").replace("/", "")
            direction = item.get("direction", "")
            if not symbol or not direction:
                continue

            conviction = item.get("conviction", 0)
            t_signal = item.get("titan_signal", "")
            reason = item.get("reason", "")

            if conviction < 50:
                rejected += 1
                continue

            row = dict(
                symbol=symbol,
                direction=direction,
                timeframe="4h",
                entry=round(float(item.get("entry", 0)), 6),
                tp=round(float(item.get("tp", 0)), 6),
                sl=round(float(item.get("sl", 0)), 6),
                conviction=conviction,
                oracle_signal="N/A",
                titan_signal=t_signal,
                oracle_score=0,
                titan_confidence=0,
                market_state="scanner",
                fired_reason=item.get("reason", ""),
                fired_at=now_ms,
                source="counter" if reason.startswith("(counter)") else "scanner",
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
        logger.info(f"Job: log_best_setups — {logged} logged, {rejected} rejected (low_conviction)")


# ---------------------------------------------------------------------------
# Job C: resolve_signal_outcomes
# ---------------------------------------------------------------------------

async def resolve_signal_outcomes(ctx):
    """
    Runs every 30min. 
    1. Fast-path: Check current ticker price for all OPEN signals.
    2. Historical: Walk candles chronologically from fired_at to catch hits during downtime.
    - WIN   — TP hit before SL
    - LOSS  — SL hit before TP
    - REVIEW — fired_at > 7 days ago, neither hit
    """
    from app.providers import get_provider
    from app.schemas.trading import Position

    logger.info("Job: resolve_signal_outcomes — checking ticker prices and historical candles...")
    
    # 1. Fast-path: Current Ticker Resolution
    provider = get_provider()
    try:
        tickers = await provider.get_all_tickers()
        if tickers:
            async with Database.get_session() as session:
                stmt = select(SignalLog).where(SignalLog.outcome == "OPEN")
                res = await session.execute(stmt)
                open_signals = res.scalars().all()
                
                now_ms = int(time.time() * 1000)
                fast_resolved = 0
                
                # Create a normalized ticker map (no slashes)
                ticker_map = {s.replace("/", ""): t for s, t in tickers.items()}
                
                for sig in open_signals:
                    ticker = ticker_map.get(sig.symbol.replace("/", ""))
                    if not ticker or "last" not in ticker:
                        continue
                        
                    price = float(ticker["last"])
                    new_outcome = None
                    
                    if sig.direction == "LONG":
                        if sig.tp > 0 and price >= sig.tp:
                            new_outcome = "WIN"
                        elif sig.sl > 0 and price <= sig.sl:
                            new_outcome = "LOSS"
                    else:  # SHORT
                        if sig.tp > 0 and price <= sig.tp:
                            new_outcome = "WIN"
                        elif sig.sl > 0 and price >= sig.sl:
                            new_outcome = "LOSS"
                            
                    if new_outcome:
                        sig.outcome = new_outcome
                        sig.resolved_at = now_ms
                        sig.resolved_price = price
                        sig.regime_at_resolution = await _get_market_state()
                        sig.time_to_resolution_ms = now_ms - sig.fired_at
                        session.add(sig)
                        fast_resolved += 1
                        
                        # Bridge to Position
                        pos_stmt = select(Position).where(
                            Position.signal_log_id == sig.id,
                            Position.status.in_(["PENDING", "OPEN"])
                        )
                        pos_res = await session.execute(pos_stmt)
                        linked_pos = pos_res.scalars().first()
                        if linked_pos:
                            # Close linked position logic (same as historical)
                            entry = linked_pos.actual_entry or linked_pos.intended_entry
                            if linked_pos.direction == "LONG":
                                raw_pnl = (price - entry) * linked_pos.quantity
                            else:
                                raw_pnl = (entry - price) * linked_pos.quantity
                            
                            linked_pos.actual_exit = price
                            linked_pos.status = "CLOSED"
                            linked_pos.closed_at = now_ms
                            linked_pos.pnl_usd = raw_pnl - (price * linked_pos.quantity * 0.001)
                            linked_pos.pnl_pct = (raw_pnl / (entry * linked_pos.quantity)) * 100
                            linked_pos.outcome = new_outcome
                            session.add(linked_pos)

                if fast_resolved:
                    await session.commit()
                    logger.info(f"Fast-path resolution: {fast_resolved} signal(s) resolved via ticker")
    except Exception as e:
        logger.warning(f"Ticker resolution failed: {e}")
    finally:
        await provider.close()

    # 2. Historical Resolution (to catch hits that happened between scans)
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
    from app.providers import get_provider

    logger.info("Job: resolve_outcomes_historical — checking open signals with candle data...")

    config = await _get_config()
    now_ms = int(time.time() * 1000)
    review_threshold_ms = config["review_days"] * 24 * 60 * 60 * 1000
    resolved = 0

    async with Database.get_session() as session:
        stmt = select(SignalLog).where(SignalLog.outcome == "OPEN")
        result = await session.execute(stmt)
        open_signals = result.scalars().all()

        # Fetch candles once per unique symbol (always include BTC for resolution context)
        # Share one provider to avoid repeated exchangeInfo calls
        unique_symbols = {sig.symbol for sig in open_signals}
        unique_symbols.add("BTCUSDT")
        candle_cache = {}
        shared_provider = get_provider()
        try:
            for sym in unique_symbols:
                df = await get_candles_df(sym, timeframe="4h", limit=300, provider=shared_provider)
                if df is not None and not df.empty:
                    candle_cache[sym] = df
        finally:
            await shared_provider.close()

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
                fired_ts = pd.Timestamp(sig.fired_at, unit="ms")
                candles_after = df[df["timestamp"] >= fired_ts].sort_values("timestamp")

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
                    c_ts = candle.get("timestamp", 0)
                    c_time = int(c_ts.timestamp() * 1000) if hasattr(c_ts, "timestamp") else int(c_ts)

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
                        # Both hit in same 4H candle — fetch 5min candles
                        # to determine which level was actually hit first.
                        # Pass provider=None so get_candles_df manages its own
                        # lifecycle (shared_provider is already closed at this point).
                        tiebreak = await _resolve_tiebreaker_5m(
                            sig.symbol, sig.direction, sig.tp, sig.sl,
                            c_time,
                        )
                        new_outcome = tiebreak["outcome"]
                        resolved_price = tiebreak["resolved_price"]
                        c_time = tiebreak.get("resolved_at_ms", c_time)
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
                    sig.regime_at_resolution = await _get_market_state()
                    sig.time_to_resolution_ms = resolved_at_ms - sig.fired_at

                    # BTC price at resolution (from cached BTC candles)
                    btc_df = candle_cache.get("BTCUSDT")
                    if btc_df is not None and not btc_df.empty:
                        resolved_ts = pd.Timestamp(resolved_at_ms, unit="ms")
                        btc_at = btc_df[btc_df["timestamp"] <= resolved_ts]
                        if not btc_at.empty:
                            sig.btc_price_at_resolution = round(float(btc_at.iloc[-1]["close"]), 2)

                    session.add(sig)
                    resolved += 1

                    # Bridge: close linked position if one exists
                    try:
                        pos_result = await session.execute(
                            select(Position).where(
                                Position.signal_log_id == sig.id,
                                Position.status.in_(["PENDING", "OPEN"]),
                            )
                        )
                        linked_pos = pos_result.scalars().first()
                        if linked_pos:
                            if linked_pos.status == "PENDING":
                                linked_pos.status = "CANCELLED"
                                linked_pos.outcome = "EXPIRED"
                            else:
                                # OPEN position — close with PnL
                                FEE_PCT = 0.001
                                entry = linked_pos.actual_entry or linked_pos.intended_entry
                                if linked_pos.direction == "LONG":
                                    raw_pnl = (resolved_price - entry) * linked_pos.quantity
                                else:
                                    raw_pnl = (entry - resolved_price) * linked_pos.quantity
                                fee = linked_pos.quote_amount * FEE_PCT
                                pnl_usd = raw_pnl - fee
                                pnl_pct = (pnl_usd / linked_pos.quote_amount * 100) if linked_pos.quote_amount > 0 else 0.0
                                linked_pos.status = "CLOSED"
                                linked_pos.outcome = new_outcome
                                linked_pos.actual_exit = resolved_price
                                linked_pos.pnl_usd = round(pnl_usd, 4)
                                linked_pos.pnl_pct = round(pnl_pct, 2)
                                linked_pos.market_state_at_close = sig.regime_at_resolution or ""

                            linked_pos.closed_at = resolved_at_ms
                            session.add(linked_pos)

                            # Log trade event so it shows in trade history
                            import json as _json
                            event_type = "TP_HIT" if new_outcome == "WIN" else "SL_HIT"
                            event = TradeEvent(
                                position_id=linked_pos.id,
                                event_type=event_type,
                                details=_json.dumps({
                                    "exit_price": resolved_price,
                                    "pnl_usd": linked_pos.pnl_usd,
                                    "pnl_pct": linked_pos.pnl_pct,
                                    "source": "signal_resolution",
                                }),
                                timestamp=resolved_at_ms,
                            )
                            session.add(event)
                            logger.info(
                                f"Historical resolve: closed position #{linked_pos.id} "
                                f"{linked_pos.symbol} {linked_pos.direction} → {new_outcome} "
                                f"pnl=${linked_pos.pnl_usd}"
                            )
                    except Exception as pos_err:
                        logger.warning(f"Historical resolve: position bridge error for {sig.symbol}: {pos_err}")

                    try:
                        from app.schemas.activity_log import log_activity
                        await log_activity("OUTCOME_RESOLVED",
                                          symbol=sig.symbol,
                                          direction=sig.direction,
                                          outcome=new_outcome,
                                          resolved_price=resolved_price,
                                          regime_at_resolution=sig.regime_at_resolution,
                                          time_to_resolution_ms=sig.time_to_resolution_ms,
                                          method="historical_candle")
                    except Exception as act_err:
                        logger.warning(f"Historical resolve: activity log failed for {sig.symbol}: {act_err}")

                    logger.info(
                        f"Historical resolve: {sig.symbol} {sig.direction} → {new_outcome} "
                        f"@ {resolved_price} regime={sig.regime_at_resolution} "
                        f"ttf={sig.time_to_resolution_ms}ms"
                    )

            except Exception as e:
                logger.warning(f"Historical resolve error for {sig.symbol}: {e}")

        if resolved:
            await session.commit()

    logger.info(f"Job: resolve_outcomes_historical complete — {resolved} signal(s) resolved")


# ---------------------------------------------------------------------------
# Job E: log_contrarian_signals
# ---------------------------------------------------------------------------

async def log_contrarian_signals(ctx):
    """
    Identifies overextended coins (3x ATR from EMA200) and logs them to SignalLog.
    Runs every hour.
    """
    from app.services.market_data import MarketDataService
    from app.routes.analytics import fetch_all_candles
    from app.indicators.mean_reversion import detect_mean_reversion
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    
    logger.info("Job: log_contrarian_signals — scanning for extensions...")
    
    # 1. Fetch top 50 symbols
    symbols = await MarketDataService.get_top_symbols(limit=50)
    
    # 2. Fetch 1H candles
    df_data = await fetch_all_candles(symbols, timeframe="1h")
    
    rows_to_insert = []
    now_ms = int(time.time() * 1000)
    
    for sym, df in df_data.items():
        if df is None or df.empty:
            continue
            
        rev = detect_mean_reversion(df)
        if rev.get('is_extended'):
            direction = "LONG" if rev['opportunity'] == "SPOT_BUY" else "SHORT"
            
            # Use 1.5 ATR for SL, Reversion to mean for TP
            price = rev['price']
            mean = rev['mean']
            # Calculate ATR for SL
            import pandas_ta as ta
            atr_series = ta.atr(df['high'], df['low'], df['close'], length=14)
            if atr_series is None or atr_series.empty:
                continue
            atr = float(atr_series.iloc[-1])
            
            sl = price - (1.5 * atr) if direction == "LONG" else price + (1.5 * atr)
            tp = mean
            
            rows_to_insert.append(dict(
                symbol=sym,
                direction=direction,
                timeframe="1h",
                entry=round(price, 6),
                tp=round(tp, 6),
                sl=round(sl, 6),
                conviction=70,  # Base conviction for contrarian
                oracle_signal="N/A",
                titan_signal="CONTRARIAN",
                oracle_score=0,
                titan_confidence=int(rev['extension_atr'] * 10), # Pseudo-confidence
                market_state=await _get_market_state(),
                fired_reason=f"(contrarian) {rev['extension_atr']}x ATR extension",
                fired_at=now_ms,
                source="counter",
                provider="binance",
                outcome="OPEN",
            ))

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
            logger.info(f"Job: log_contrarian_signals — {len(rows_to_insert)} logged")

