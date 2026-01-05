import asyncio
import logging
from arq import cron
from app.storage import RedisClient, Database
from app.providers.binance_provider import BinanceProvider
from app.schemas.market_data import MarketSummary, MarketTicker

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Provider Instance
provider = None

async def startup(ctx):
    """Initialize resources on worker startup"""
    global provider
    logger.info("Worker starting up...")
    Database.init()
    await Database.create_tables()
    provider = BinanceProvider() 
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
        # Fetch all tickers from Binance
        tickers = await provider.get_all_tickers()
        
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

# --- Worker Settings ---

from arq.connections import RedisSettings
import os
from urllib.parse import urlparse

class WorkerSettings:
    # Only the market summary job is needed now
    # Historical candle data is fetched on-demand by the API
    functions = [sync_market_summary]
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

    # Cron: Only market summary every 30 seconds
    cron_jobs = [
        cron(sync_market_summary, second={0, 30}),
    ]

if __name__ == "__main__":
    import asyncio
    from arq import run_worker
    asyncio.run(run_worker(WorkerSettings))
