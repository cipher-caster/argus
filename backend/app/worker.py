import asyncio
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from arq import cron
from app.storage import RedisClient, Database
from app.providers import get_provider
from app.providers.binance_provider import BinanceProvider
from app.providers.okx_provider import OKXProvider
from app.schemas.market_data import MarketSummary, MarketTicker
from app.utils.trading_utils import calculate_conviction

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _retry(coro_fn, retries: int = 3, delay: float = 2.0, label: str = ""):
    """Run an async callable with simple linear retry on exception."""
    for attempt in range(1, retries + 1):
        try:
            return await coro_fn()
        except Exception as e:
            if attempt == retries:
                logger.error(f"{label} failed after {retries} attempts: {e}", exc_info=True)
                raise
            logger.warning(f"{label} attempt {attempt}/{retries} failed: {e} — retrying in {delay}s")
            await asyncio.sleep(delay)

# Global Provider Instance (hot-swappable based on Redis config)
provider = None
_active_provider = None
_active_provider_name = None
_provider_unavailable_until: float = 0  # epoch seconds; 0 = not in backoff
_PROVIDER_BACKOFF_SECONDS = 300  # retry unavailable provider every 5 min


async def get_active_provider():
    """Return the provider matching the current Redis config, rebuilding only on change."""
    global _active_provider, _active_provider_name
    r = RedisClient.get_instance()
    config_name = await r.get("config:provider")
    target = config_name or os.getenv("DATA_PROVIDER", "binance")
    if _active_provider_name != target:
        if _active_provider:
            await _active_provider.close()
        _active_provider = BinanceProvider() if target == "binance" else OKXProvider()
        _active_provider_name = target
        logger.info(f"Worker provider set to {target}")
    return _active_provider

async def _recover_missed_scans(ctx, missed_closes: list):
    """Recover signals from missed 4H candle closes during downtime.
    Uses regime-based filtering (same as log_watchlist_setups)."""
    from app.routes.strategy import get_candles_df, titan
    from app.jobs.signal_log import _get_config
    from app.schemas.activity_log import log_activity
    from sqlalchemy import text
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from app.schemas.signal_log import SignalLog

    config = await _get_config()
    recovered = 0

    # Share one provider across all fetches to avoid repeated exchangeInfo calls
    shared_provider = get_provider()

    try:
        # Detect regime once (BTC weekly EMA50)
        regime = "UNKNOWN"
        try:
            import pandas_ta
            btc_df = await get_candles_df("BTC/USDT", timeframe="1w", limit=60, provider=shared_provider)
            if btc_df is not None and not btc_df.empty and "close" in btc_df.columns:
                ema50 = pandas_ta.ema(btc_df["close"], length=50)
                if ema50 is not None and not ema50.empty:
                    last_ema = ema50.iloc[-1]
                    last_close = float(btc_df.iloc[-1]["close"])
                    if not (last_ema != last_ema):  # NaN check
                        regime = "BULL" if last_close > float(last_ema) else "BEAR"
        except Exception as e:
            logger.warning(f"Recovery: regime detection failed: {e}")

        for close_dt in missed_closes:
            close_ms = int(close_dt.timestamp() * 1000)

            for symbol in config["watchlist"]:
                try:
                    df = await get_candles_df(symbol, timeframe="4h", limit=300, provider=shared_provider)
                    if df is None or df.empty:
                        continue

                    t = titan.analyze(df, symbol=symbol)
                    if "error" in t:
                        continue

                    t_signal = t.get("signal", "")
                    t_confidence = t.get("confidence", 0)

                    is_long = t_signal in ("BUY", "BUY_LIMIT", "STRONG_BUY")
                    is_short = t_signal in ("SELL", "SELL_LIMIT", "STRONG_SELL")
                    if not (is_long or is_short) or t_confidence < config["min_titan_confidence"]:
                        continue

                    # Regime-based direction filtering
                    if regime == "BEAR" and is_long:
                        continue
                    if regime == "BULL" and is_short:
                        continue

                    # Conviction: 60% Titan + 20% regime bonus + 10% signal type
                    regime_aligned = (regime == "BULL" and is_long) or (regime == "BEAR" and is_short)
                    conviction = calculate_conviction(
                        confidence=t_confidence,
                        regime_aligned=regime_aligned,
                        is_market_signal=t_signal in ("BUY", "SELL", "STRONG_BUY", "STRONG_SELL"),
                    )

                    targets = t.get("targets", {})
                    price = float(df.iloc[-1]["close"])
                    reasons = t.get("reasons", [])
                    direction = "LONG" if is_long else "SHORT"
                    reg_tag = "trend" if regime_aligned else "counter"
                    fired_reason = f"[RECOVERED] ({reg_tag}) {t_signal} {t_confidence}% | " + " | ".join(reasons[:2])

                    row = dict(
                        symbol=symbol,
                        direction=direction,
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
                        fired_at=close_ms,
                        source="live",
                        outcome="OPEN",
                    )

                    async with Database.get_session() as session:
                        stmt = (
                            pg_insert(SignalLog)
                            .values(**row)
                            .on_conflict_do_nothing(
                                index_elements=["symbol", "direction"],
                                index_where=text("outcome = 'OPEN'"),
                            )
                        )
                        result = await session.execute(stmt)
                        await session.commit()

                        if result.rowcount > 0:
                            recovered += 1
                            await log_activity("SIGNAL_RECOVERED",
                                               symbol=symbol,
                                               direction=direction,
                                               conviction=conviction,
                                               candle_close=close_dt.isoformat())
                            logger.info(f"Recovery: {symbol} {direction} signal recovered from {close_dt}")

                except Exception as e:
                    logger.warning(f"Recovery error for {symbol} at {close_dt}: {e}")
    finally:
        await shared_provider.close()

    if recovered:
        await log_activity("RECOVERY_SCAN", severity="INFO",
                           signals_recovered=recovered,
                           message=f"Recovered {recovered} signal(s) from {len(missed_closes)} missed candle close(s)")

    logger.info(f"Startup: recovery complete — {recovered} signal(s) recovered")


async def startup(ctx):
    """Initialize resources on worker startup"""
    global provider
    logger.info("Worker starting up...")
    Database.init()
    await Database.create_tables()
    provider = get_provider()
    ctx['provider'] = provider
    logger.info("Worker initialized and ready.")
    # Run initial signal scan so data is available immediately on app open
    # (cron only fires at 4H candle closes, so without this there's a gap)
    try:
        await log_watchlist_setups(ctx)
        await resolve_signal_outcomes(ctx)
        logger.info("Startup: initial signal scan complete")
    except Exception as e:
        logger.warning(f"Startup: initial signal scan failed (non-fatal): {e}")

    # Recover active trading positions on startup
    try:
        await manage_positions(ctx)
        logger.info("Startup: position recovery complete")
    except Exception as e:
        logger.warning(f"Startup: position recovery failed (non-fatal): {e}")

    # --- Startup Recovery ---
    try:
        r = RedisClient.get_instance()
        last_heartbeat = await r.get("worker:heartbeat")

        if last_heartbeat:
            last_ms = int(last_heartbeat)
            now_ms = int(time.time() * 1000)
            gap_ms = now_ms - last_ms
            gap_hours = gap_ms / (1000 * 60 * 60)

            if gap_hours > 0.5:  # Only recover if gap > 30 minutes
                logger.info(f"Startup: detected {gap_hours:.1f}h gap since last heartbeat")

                # Log the gap
                from app.schemas.activity_log import log_activity
                await log_activity("HEARTBEAT_GAP", severity="WARN",
                                   gap_hours=round(gap_hours, 1),
                                   last_heartbeat_ms=last_ms)

                # Calculate missed 4H candle closes (00, 04, 08, 12, 16, 20 UTC)
                last_dt = datetime.fromtimestamp(last_ms / 1000, tz=timezone.utc)
                now_dt = datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc)

                missed_closes = []
                candle_hours = [0, 4, 8, 12, 16, 20]
                check_dt = last_dt.replace(minute=0, second=0, microsecond=0)
                while check_dt <= now_dt:
                    if check_dt.hour in candle_hours and check_dt > last_dt:
                        missed_closes.append(check_dt)
                    check_dt = check_dt + timedelta(hours=1)

                if missed_closes:
                    logger.info(f"Startup: {len(missed_closes)} missed 4H candle close(s), recovering signals...")
                    await log_activity("RECOVERY_SCAN",
                                       missed_closes=len(missed_closes),
                                       first_missed=missed_closes[0].isoformat(),
                                       last_missed=missed_closes[-1].isoformat())

                    # For each missed close, run signal scan with historical data
                    await _recover_missed_scans(ctx, missed_closes)

                    # Resolve any open signals using candle high/low (not just current price)
                    from app.jobs.signal_log import resolve_outcomes_historical
                    await resolve_outcomes_historical(ctx)
                else:
                    logger.info("Startup: no missed 4H candle closes")
        else:
            logger.info("Startup: no previous heartbeat found (first boot)")
            from app.schemas.activity_log import log_activity
            await log_activity("STARTUP", message="First boot — no recovery needed")

        # Update heartbeat
        await r.set("worker:heartbeat", str(int(time.time() * 1000)))

    except Exception as e:
        logger.warning(f"Startup: recovery failed (non-fatal): {e}")

    # Execute any new signals (including recovered ones) into paper trades
    try:
        await execute_signals(ctx)
        logger.info("Startup: signal execution complete")
    except Exception as e:
        logger.warning(f"Startup: signal execution failed (non-fatal): {e}")

    from app.schemas.activity_log import log_activity
    await log_activity("STARTUP", message="Worker started successfully")


async def shutdown(ctx):
    """Cleanup on worker shutdown"""
    global provider
    logger.info("Worker shutting down...")
    try:
        from app.schemas.activity_log import log_activity
        await log_activity("SHUTDOWN", message="Worker shutting down")
    except Exception:
        pass  # DB may already be closing
    if provider:
        await provider.close()
    await Database.close()
    await RedisClient.close()
    logger.info("Worker shutdown complete.")

# --- Jobs ---

async def sync_market_summary(ctx):
    """
    Fetch market data from Binance and cache in Redis.
    
    This job runs every 30 seconds and populates:
    - market:summary - Top gainers, losers, volume leaders
    - market:tickers - All USDT ticker prices (used by /api/ticker and /api/market/coins)
    """
    provider = ctx['provider']
    logger.info("Job: Syncing Market Summary...")
    
    try:
        import time
        global _provider_unavailable_until

        active = await get_active_provider()
        in_backoff = active.name != "binance" and time.time() < _provider_unavailable_until

        if in_backoff:
            # Primary provider is in cooldown — use Binance directly, no timeout wait
            fallback = BinanceProvider()
            try:
                tickers = await _retry(
                    lambda: fallback.get_all_tickers(),
                    retries=3,
                    delay=2.0,
                    label="sync_market_summary:fallback:get_all_tickers",
                )
            finally:
                await fallback.close()
        else:
            try:
                tickers = await _retry(
                    lambda: active.get_all_tickers(),
                    retries=3,
                    delay=2.0,
                    label="sync_market_summary:get_all_tickers",
                )
                _provider_unavailable_until = 0  # clear backoff on success
            except Exception as provider_err:
                if active.name != "binance":
                    _provider_unavailable_until = time.time() + _PROVIDER_BACKOFF_SECONDS
                    logger.warning(
                        f"Job: {active.name} unavailable ({provider_err}), "
                        f"falling back to Binance for {_PROVIDER_BACKOFF_SECONDS // 60}m"
                    )
                    fallback = BinanceProvider()
                    try:
                        tickers = await _retry(
                            lambda: fallback.get_all_tickers(),
                            retries=3,
                            delay=2.0,
                            label="sync_market_summary:fallback:get_all_tickers",
                        )
                    finally:
                        await fallback.close()
                else:
                    raise
        
        # Convert to list of MarketTicker objects (USDT pairs only)
        ticker_list = []
        for symbol, data in tickers.items():
            if not symbol.endswith('/USDT'): 
                continue
            
            ticker_list.append(MarketTicker(
                symbol=symbol,
                price=data.get('last') or 0.0,
                change_24h=data.get('percentage') or 0.0,
                volume_24h=data.get('quoteVolume') or 0.0,
                high_24h=data.get('high') or 0.0,
                low_24h=data.get('low') or 0.0,
            ))
            
        # Optimization: Keep only Top 250 by Volume
        # This prevents storing thousands of low-liquidity pairs
        ticker_list.sort(key=lambda x: x.volume_24h or 0, reverse=True)
        ticker_list = ticker_list[:250]
            
        # Sort for summary views
        gainers = sorted(ticker_list, key=lambda x: x.change_24h or -999, reverse=True)[:50]
        losers = sorted(ticker_list, key=lambda x: x.change_24h or 999, reverse=False)[:50]
        top_vol = sorted(ticker_list, key=lambda x: x.volume_24h or -1, reverse=True)[:50]
        
        summary = MarketSummary(
            gainers=gainers,
            losers=losers,
            top_volume=top_vol,
            timestamp=0
        )
        
        # Cache in Redis
        await RedisClient.set_json("market:summary", summary.model_dump(), ttl=60)
        await RedisClient.set_json("market:tickers", [t.model_dump() for t in ticker_list], ttl=60)
        
        logger.info(f"Job: Market Summary Synced ({len(ticker_list)} tickers)")

        # Heartbeat: record last successful sync timestamp
        r = RedisClient.get_instance()
        await r.set("worker:heartbeat", str(int(time.time() * 1000)))

    except Exception as e:
        logger.error(f"Job Failed: sync_market_summary: {e}", exc_info=True)

async def sync_market_snapshot(ctx):
    """
    Fetch comprehensive market data (Top 500) from CoinGecko.
    
    This forms the "Base State" of the market (prices, mcap, volume).
    Runs every 5 minutes.
    """
    import httpx
    logger.info("Job: Syncing Market Snapshot (CoinGecko)...")
    
    base_url = "https://api.coingecko.com/api/v3/coins/markets"
    all_coins = []
    
    try:
        async with httpx.AsyncClient() as client:
            # Fetch 1 page (250 coins) - Optimized to save API calls
            for page in range(1, 2):
                params = {
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 250,
                    "page": page,
                    "sparkline": "true",
                    "price_change_percentage": "1h,7d"
                }

                resp = await _retry(
                    lambda: client.get(base_url, params=params, timeout=30.0),
                    retries=3,
                    delay=2.0,
                    label=f"sync_market_snapshot:coingecko:page{page}",
                )
                if resp.status_code == 200:
                    data = resp.json()
                    all_coins.extend(data)
                    # Small delay to be polite to API
                    await asyncio.sleep(1.0)
                else:
                    logger.error(f"CoinGecko API Error (Page {page}): {resp.status_code}")
                    break
        
        if all_coins:
            # Transform to standard structure
            snapshot = []
            for coin in all_coins:
                sparkline = coin.get("sparkline_in_7d", {}).get("price", [])
                
                snapshot.append({
                    "symbol": coin["symbol"].upper() + "/USDT",
                    "price": coin["current_price"],
                    "change_1h": coin.get("price_change_percentage_1h_in_currency"),
                    "change_24h": coin["price_change_percentage_24h"],
                    "change_7d": coin.get("price_change_percentage_7d_in_currency"),
                    "volume_24h": coin["total_volume"],
                    "market_cap": coin["market_cap"],
                    "rank": coin["market_cap_rank"],
                    "image": coin["image"],
                    "name": coin["name"],
                    "sparkline_in_7d": sparkline
                })
                
            await RedisClient.set_json("market:snapshot", snapshot, ttl=600)
            logger.info(f"Job: Market Snapshot Synced ({len(snapshot)} coins)")
            
    except Exception as e:
        logger.error(f"Job Failed: sync_market_snapshot: {e}")

async def sync_analytics_cache(ctx):
    """
    Pre-compute and cache best-setups for the dashboard.
    Runs every 5 minutes, offset from snapshot job.
    """
    import time
    from app.routes.analytics import get_best_setups, get_oracle_signal_summary

    # Make get_provider() inside analytics functions use the effective provider.
    effective = (
        "binance"
        if _active_provider_name != "binance" and time.time() < _provider_unavailable_until
        else (_active_provider_name or os.getenv("DATA_PROVIDER", "binance"))
    )
    os.environ["DATA_PROVIDER"] = effective
    logger.info(f"Job: Pre-warming Analytics Cache (provider={effective})...")

    try:
        await _retry(
            lambda: get_oracle_signal_summary(),
            retries=3,
            delay=2.0,
            label="sync_analytics_cache:get_oracle_signal_summary",
        )
        await _retry(
            lambda: get_best_setups(timeframe="4h", limit=100),
            retries=3,
            delay=2.0,
            label="sync_analytics_cache:get_best_setups",
        )
        logger.info("Job: Analytics cache warmed (signal-summary + best-setups 4h)")
    except Exception as e:
        logger.warning(f"Cache warm failed: {e}")

    logger.info("Job: Analytics Cache Pre-warm Complete")

# --- Worker Settings ---

from arq.connections import RedisSettings
import os
from urllib.parse import urlparse
from app.jobs.signal_log import log_watchlist_setups, log_best_setups, resolve_signal_outcomes, log_contrarian_signals
from app.jobs.snapshot import snapshot_signal_outcomes
from app.trading.orchestrator import TradeOrchestrator, get_trading_config, _get_prices

_trade_orchestrator = TradeOrchestrator()


async def execute_signals(ctx):
    """
    Pick up new OPEN signals (live + scanner) and create PENDING positions via the orchestrator.
    Runs every 5 minutes to catch scanner signals promptly.
    """
    from sqlalchemy import select
    from app.schemas.signal_log import SignalLog
    from app.schemas.trading import Position
    from app.jobs.signal_log import _get_config as _get_signal_config

    config = await get_trading_config()
    if not config.get("enabled", False):
        return

    logger.info("Job: execute_signals — processing new signals...")

    # Only trade watchlist coins — scanner logs everything for scouting,
    # but only watchlist-approved symbols get passed to the orchestrator.
    signal_config = await _get_signal_config()
    watchlist = set(signal_config["watchlist"])

    async with Database.get_session() as session:
        # Signals that are OPEN and have no Position yet (live + scanner sources)
        result = await session.execute(
            select(SignalLog).where(
                SignalLog.outcome == "OPEN",
                SignalLog.source.in_(["live", "scanner"]),
                ~SignalLog.id.in_(
                    select(Position.signal_log_id).where(
                        Position.signal_log_id.is_not(None)
                    )
                ),
            )
        )
        new_signals = result.scalars().all()

    # Filter to watchlist only — non-watchlist scanner signals are tracked but not traded
    tradeable = [s for s in new_signals if s.symbol in watchlist]
    skipped = len(new_signals) - len(tradeable)
    if skipped:
        logger.info(f"Job: execute_signals — {skipped} signal(s) skipped (not in watchlist)")

    logger.info(f"Job: execute_signals — {len(tradeable)} tradeable signal(s) found")
    batch_positions = []
    for signal in tradeable:
        try:
            pos = await _trade_orchestrator.process_signal(signal, batch_positions=batch_positions)
            if pos is not None:
                batch_positions.append(pos)
        except Exception as e:
            logger.warning(f"execute_signals error for {signal.symbol}: {e}")


async def manage_positions(ctx):
    """
    Check fills and TP/SL hits on all active positions. Runs every 5 minutes.
    """
    config = await get_trading_config()
    if not config.get("enabled", False):
        return

    prices = await _get_prices()

    logger.info("Job: manage_positions — checking active positions...")
    try:
        await _trade_orchestrator.check_pending_fills(config=config, prices=prices)
        await _trade_orchestrator.check_open_positions(config=config, prices=prices)
        await _trade_orchestrator.check_circuit_breaker(config=config)
    except Exception as e:
        logger.error(f"Job Failed: manage_positions: {e}", exc_info=True)


async def sync_trading_balance(ctx):
    """
    Cache current portfolio balance in Redis for quick API access. Runs every 10 minutes.
    """
    config = await get_trading_config()
    if not config.get("enabled", False):
        return
    try:
        from app.trading.portfolio import PortfolioTracker
        portfolio = PortfolioTracker(config["initial_capital"])
        balance = await portfolio.get_balance()
        await RedisClient.set_json("trading:balance", {"balance": round(balance, 2)}, ttl=300)
        logger.info(f"Job: sync_trading_balance — ${balance:.2f}")
    except Exception as e:
        logger.error(f"Job Failed: sync_trading_balance: {e}")


_OKX_BACKFILL_TIMEFRAMES = ["15m", "1h", "4h", "1d"]
_OKX_BACKFILL_DAYS = 7


async def backfill_okx_candles(ctx) -> None:
    """
    Backfill last 7 days of OKX OHLCV data for all watchlist symbols.
    Runs daily at 02:00 UTC to keep candle history current.
    """
    from app.jobs.signal_log import _get_config
    from app.schemas.activity_log import log_activity
    from app.schemas.candle import Candle

    logger.info("Job: backfill_okx_candles — starting daily OKX backfill...")

    config = await _get_config()
    watchlist = config.get("watchlist", [])
    symbols = [f"{s.replace('USDT', '')}/USDT" for s in watchlist]

    since_ms = int((datetime.now(timezone.utc) - timedelta(days=_OKX_BACKFILL_DAYS)).timestamp() * 1000)
    limit = _OKX_BACKFILL_DAYS * 24 * 4  # generous upper bound (covers 15m candles for 7d)

    okx = OKXProvider()
    total = 0
    errors = 0

    try:
        for symbol in symbols:
            for timeframe in _OKX_BACKFILL_TIMEFRAMES:
                try:
                    candles_data = await _retry(
                        lambda s=symbol, tf=timeframe: okx.get_ohlcv(s, timeframe=tf, limit=limit, since=since_ms),
                        retries=3,
                        delay=2.0,
                        label=f"backfill_okx_candles:{symbol}:{timeframe}",
                    )

                    if not candles_data:
                        continue

                    async with Database.get_session() as session:
                        for c in candles_data:
                            candle_db = Candle(
                                symbol=symbol,
                                provider="okx",
                                timeframe=timeframe,
                                timestamp=c.timestamp,
                                open=c.open,
                                high=c.high,
                                low=c.low,
                                close=c.close,
                                volume=c.volume,
                            )
                            await session.merge(candle_db)
                        await session.commit()

                    total += len(candles_data)

                except Exception as e:
                    errors += 1
                    logger.warning(f"backfill_okx_candles: {symbol} {timeframe} failed: {e}")

                await asyncio.sleep(0.3)

    except Exception as e:
        logger.error(f"Job Failed: backfill_okx_candles: {e}", exc_info=True)
    finally:
        await okx.close()

    if errors:
        logger.warning(f"Job: backfill_okx_candles — complete with {errors} error(s), {total} candles stored")
        await log_activity(
            "OKX_BACKFILL",
            severity="WARN",
            candles_stored=total,
            errors=errors,
            symbols=len(symbols),
            message=f"OKX backfill complete with {errors} error(s)",
        )
    else:
        logger.info(f"Job: backfill_okx_candles — complete, {total} candles stored across {len(symbols)} symbols")
        await log_activity(
            "OKX_BACKFILL",
            candles_stored=total,
            symbols=len(symbols),
            message=f"OKX backfill complete",
        )


class WorkerSettings:
    # Market data and analytics cache jobs
    functions = [
        sync_market_summary, sync_market_snapshot, sync_analytics_cache,
        log_watchlist_setups, log_best_setups, resolve_signal_outcomes,
        execute_signals, manage_positions, sync_trading_balance,
        log_contrarian_signals, backfill_okx_candles, snapshot_signal_outcomes,
    ]
    on_startup = startup
    on_shutdown = shutdown

    # Default local Redis
    redis_settings = RedisSettings(host='localhost', port=6379)

    # Override from environment
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        url = urlparse(redis_url)
        redis_settings = RedisSettings(
            host=url.hostname,
            port=url.port,
            password=url.password,
            database=0
        )

    # Jobs
    cron_jobs = [
        cron(sync_market_summary, second={0}),  # Live data every 60s
        cron(sync_market_snapshot, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),  # Snapshot (CoinGecko) every 5m
        cron(sync_analytics_cache, minute={2, 7, 12, 17, 22, 27, 32, 37, 42, 47, 52, 57}),  # Analytics every 5m (offset)
        cron(log_watchlist_setups, hour={0, 4, 8, 12, 16, 20}, minute={3}),  # Signal log at each 4H candle close (+3m for data)
        cron(log_best_setups, minute={3, 8, 13, 18, 23, 28, 33, 38, 43, 48, 53, 58}),  # Scanner signals → signal_log
        cron(log_contrarian_signals, minute={0, 10, 20, 30, 40, 50}),  # Contrarian radar every 10m
        cron(resolve_signal_outcomes, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),  # Resolve every 5m (fast-path)
        cron(execute_signals, minute={5, 15, 25, 35, 45, 55}),  # Execute signals every 10min
        cron(manage_positions, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),  # Check fills/TP/SL every 5min
        cron(sync_trading_balance, minute={1, 11, 21, 31, 41, 51}),  # Cache balance every 10min
        cron(backfill_okx_candles, minute={0, 30}),  # OKX candle backfill every 30 min
        cron(snapshot_signal_outcomes, hour={0}, minute={5}),  # Daily outcome snapshot at 00:05 UTC
    ]

if __name__ == "__main__":
    import asyncio
    from arq import run_worker
    asyncio.run(run_worker(WorkerSettings))

