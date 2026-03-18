import asyncio
import logging
import os
from arq import cron
from app.storage import RedisClient, Database
from app.providers import get_provider
from app.providers.binance_provider import BinanceProvider
from app.providers.okx_provider import OKXProvider
from app.schemas.market_data import MarketSummary, MarketTicker

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

async def startup(ctx):
    """Initialize resources on worker startup"""
    global provider
    logger.info("Worker starting up...")
    Database.init()
    await Database.create_tables()
    provider = get_provider()
    ctx['provider'] = provider
    logger.info("Worker initialized and ready.")
    # Note: Historical candle data is now fetched on-demand by the API
    # Run backfill_history.py script manually for initial data population

async def shutdown(ctx):
    """Cleanup on worker shutdown"""
    global provider
    logger.info("Worker shutting down...")
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
                tickers = await fallback.get_all_tickers()
            finally:
                await fallback.close()
        else:
            try:
                tickers = await active.get_all_tickers()
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
                        tickers = await fallback.get_all_tickers()
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
                
                resp = await client.get(base_url, params=params, timeout=30.0)
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
    Pre-compute and cache analytics for common timeframes.
    This makes initial page loads instant instead of waiting for live data.
    Runs every 5 minutes, offset from snapshot job.
    """
    import time
    from app.routes.analytics import (
        get_oracle_screener,
        get_contrarian_radar,
        get_oracle_signal_summary,
        get_best_setups,
        get_titan_radar,
    )

    # Make get_provider() inside analytics functions use the effective provider.
    # If the primary provider is in backoff, analytics would create a new OKX instance
    # and hang for 15s on every fetch_all_candles call (~9 calls = 135s job time).
    effective = (
        "binance"
        if _active_provider_name != "binance" and time.time() < _provider_unavailable_until
        else (_active_provider_name or os.getenv("DATA_PROVIDER", "binance"))
    )
    os.environ["DATA_PROVIDER"] = effective
    logger.info(f"Job: Pre-warming Analytics Cache (provider={effective})...")

    timeframes = ["1h", "4h", "1d"]
    for tf in timeframes:
        try:
            await get_oracle_screener(limit=50, timeframe=tf)
            await get_contrarian_radar(limit=50, timeframe=tf)
            logger.info(f"Job: Analytics cache warmed for {tf}")
        except Exception as e:
            logger.warning(f"Cache warm failed for {tf}: {e}")

    # Warm endpoints that don't vary by timeframe list but have expensive computation
    try:
        await get_oracle_signal_summary()
    except Exception as e:
        logger.warning(f"Cache warm failed for signal-summary: {e}")

    try:
        await get_best_setups(timeframe="4h", limit=50)
    except Exception as e:
        logger.warning(f"Cache warm failed for best-setups: {e}")

    try:
        await get_titan_radar(limit=50, timeframe="4h")
    except Exception as e:
        logger.warning(f"Cache warm failed for titan-radar: {e}")

    logger.info("Job: Analytics Cache Pre-warm Complete")

# --- Worker Settings ---

from arq.connections import RedisSettings
import os
from urllib.parse import urlparse
from app.jobs.signal_log import log_watchlist_setups, resolve_signal_outcomes

class WorkerSettings:
    # Market data and analytics cache jobs
    functions = [sync_market_summary, sync_market_snapshot, sync_analytics_cache, log_watchlist_setups, resolve_signal_outcomes]
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
        cron(log_watchlist_setups, minute={4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59}),  # Signal log every 5m (offset)
        cron(resolve_signal_outcomes, minute={30}),  # Resolve outcomes every hour
    ]

if __name__ == "__main__":
    import asyncio
    from arq import run_worker
    asyncio.run(run_worker(WorkerSettings))

