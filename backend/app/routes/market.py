"""
Market Data API Routes
Endpoints for fetching OHLCV data and symbol information
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.providers import SymbolInfo
from app.storage import RedisClient
from app.services.market_data import MarketDataService
from app.schemas.market_data import (
    OHLCVResponse, TickerResponse, CoinInfo, CoinsResponse, 
    MarketSummaryResponse, MarketTicker
)
from app.exceptions import DataProviderError, CacheError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["market"])

# Provider instance will be injected from main.py
_provider = None


def set_provider(provider):
    """Set the active data provider"""
    global _provider
    _provider = provider


def get_provider():
    """Get the active data provider"""
    if _provider is None:
        raise HTTPException(status_code=500, detail="Data provider not initialized")
    return _provider


@router.get("/ohlcv/{symbol:path}", response_model=OHLCVResponse)
async def get_ohlcv(
    symbol: str,
    timeframe: str = Query(default="1h", pattern="^(1m|5m|15m|30m|1h|4h|12h|1d|3d|1w)$"),
    limit: int = Query(default=100, ge=1, le=1000),
    end_timestamp: Optional[int] = Query(default=None, description="Fetch candles before this timestamp (ms)")
):
    """
    Fetch OHLCV candlestick data.
    Delegates to MarketDataService for DB/API sync.
    """
    try:
        candles, provider_name = await MarketDataService.fetch_and_sync_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            end_timestamp=end_timestamp
        )
        
        logger.info(f"Fetched {len(candles)} candles for {symbol} {timeframe}")
        
        return OHLCVResponse(
            symbol=symbol,
            timeframe=timeframe,
            provider=provider_name,
            candles=candles
        )
    except DataProviderError as e:
        logger.error(f"Provider error fetching {symbol} {timeframe}: {e}")
        raise HTTPException(status_code=503, detail=f"Data provider unavailable: {str(e)}")
    except ValidationError as e:
        logger.warning(f"Validation error for {symbol} {timeframe}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error fetching {symbol} {timeframe}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


@router.get("/symbols", response_model=List[SymbolInfo])
async def get_symbols():
    """Get list of available trading pairs"""
    provider = get_provider()
    
    try:
        symbols = await provider.get_symbols()
        logger.info(f"Fetched {len(symbols)} symbols from provider")
        return symbols
    except DataProviderError as e:
        logger.error(f"Provider error fetching symbols: {e}")
        raise HTTPException(status_code=503, detail=f"Data provider unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching symbols: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch symbols: {str(e)}")


@router.get("/ticker/{symbol:path}", response_model=TickerResponse)
async def get_ticker(symbol: str):
    """Get current price for a trading pair from Redis Cache or market:tickers"""
    try:
        # Try direct key first
        price = await RedisClient.get_json(f"ticker:{symbol}")
        if price:
            logger.debug(f"Cache hit for ticker:{symbol}")
            return TickerResponse(symbol=symbol, price=price, provider="cache")
            
        # Fallback: check market:tickers list
        all_tickers = await RedisClient.get_json("market:tickers")
        if all_tickers:
            for ticker in all_tickers:
                if ticker.get('symbol') == symbol:
                    logger.debug(f"Found {symbol} in market:tickers")
                    return TickerResponse(symbol=symbol, price=ticker.get('price'), provider="market-cache")
        
        # Still not found - return null price instead of 404
        logger.warning(f"Ticker not found for {symbol}")
        return TickerResponse(symbol=symbol, price=None, provider="not-found")
    except CacheError as e:
        logger.error(f"Cache error fetching ticker {symbol}: {e}")
        raise HTTPException(status_code=503, detail=f"Cache unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching ticker {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticker: {str(e)}")


@router.get("/provider")
async def get_provider_info():
    """Get current data provider information"""
    # Simply return generic
    return {"provider": "redis-worker"}


@router.get("/market/summary", response_model=MarketSummaryResponse)
async def get_market_summary():
    """Get market summary statistics from Redis"""
    try:
        data = await RedisClient.get_json("market:summary")
        
        if not data:
            logger.warning("Market summary cache is empty")
            return MarketSummaryResponse(total_coins=0, provider="cache-empty")

        def map_tickers(tickers):
            if not tickers: return []
            return [
                CoinInfo(
                    rank=0,
                    symbol=t['symbol'],
                    name=t['symbol'].split('/')[0],
                    price=t['price'],
                    change_24h=t.get('change_24h'),
                    volume_24h=t.get('volume_24h'),
                    high_24h=t.get('high_24h'),
                    low_24h=t.get('low_24h'),
                    market_cap=0, 
                    image=None
                ) for t in tickers
            ]

        logger.info(f"Fetched market summary with {data.get('total_coins', 0)} coins")
        
        return MarketSummaryResponse(
            total_coins=data.get('total_coins', 0),
            provider="redis-cache",
            top_gainers=map_tickers(data.get('gainers', [])),
            top_losers=map_tickers(data.get('losers', [])),
            top_volume=map_tickers(data.get('top_volume', []))
        )
    except CacheError as e:
        logger.error(f"Cache error fetching market summary: {e}")
        raise HTTPException(status_code=503, detail=f"Cache unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching market summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")


@router.get("/market/tickers")
async def get_market_tickers():
    """Get all tickers from merged cache (Base + Live)"""
    try:
        data = await MarketDataService.get_merged_market_data()
        if not data:
            logger.warning("Market tickers cache is empty")
            return {"tickers": [], "provider": "cache-empty"}
        
        logger.info(f"Fetched {len(data)} merged tickers")
        return {"tickers": data, "provider": "redis-merged"}
    except CacheError as e:
        logger.error(f"Cache error fetching tickers: {e}")
        raise HTTPException(status_code=503, detail=f"Cache unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching tickers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickers: {str(e)}")


@router.get("/market/coins", response_model=CoinsResponse)
async def get_coins(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=10, le=100),
    search: Optional[str] = Query(default=None),
    sort_by: str = Query(default="market_cap", pattern="^(symbol|price|volume_24h|change_1h|change_24h|change_7d|market_cap)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$")
):
    """
    Get paginated list of coins from Redis Cache.
    """
    try:
        # Fetch full merged list
        raw_data = await MarketDataService.get_merged_market_data()
        if not raw_data:
            logger.warning("No market data available for coins endpoint")
            return CoinsResponse(coins=[], total=0, page=page, page_size=page_size)
            
        # Delegate filtering and sorting to service
        coins, total = MarketDataService.filter_and_sort_coins(
            raw_data=raw_data,
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        logger.info(f"Fetched page {page} with {len(coins)} coins (total: {total}, search: {search})")
        
        return CoinsResponse(
            coins=coins,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except CacheError as e:
        logger.error(f"Cache error fetching coins: {e}")
        raise HTTPException(status_code=503, detail=f"Cache unavailable: {str(e)}")
    except ValidationError as e:
        logger.warning(f"Validation error in coins endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error fetching coins: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch coins: {str(e)}")
