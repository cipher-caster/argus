"""
Market Data API Routes
Endpoints for fetching OHLCV data and symbol information
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import select

from app.providers import Candle as ProviderCandle, SymbolInfo
from app.storage import RedisClient, Database
from app.schemas.candle import Candle as DbCandle

router = APIRouter(prefix="/api", tags=["market"])


class OHLCVResponse(BaseModel):
    """Response model for OHLCV endpoint"""
    symbol: str
    timeframe: str
    provider: str
    candles: List[ProviderCandle]


class TickerResponse(BaseModel):
    """Response model for ticker price"""
    symbol: str
    price: Optional[float]
    provider: str

class CoinInfo(BaseModel):
    """Coin information for display"""
    rank: int
    symbol: str
    name: str
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    market_cap: Optional[float] = None
    image: Optional[str] = None
    sparkline_in_7d: Optional[List[float]] = None

class CoinsResponse(BaseModel):
    """Paginated coins list response"""
    coins: List[CoinInfo]
    total: int
    page: int
    page_size: int

class MarketSummaryResponse(BaseModel):
    """Market summary statistics"""
    total_coins: int
    provider: str


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
    Fetch OHLCV candlestick data from Database.
    If data is missing for the requested range, fetches directly from Binance and saves to DB.
    """
    from app.providers.binance_provider import BinanceProvider
    from app.schemas.candle import Candle as CandleModel
    
    try:
        async with Database.get_session() as session:
            # Base query
            query = select(DbCandle).where(
                DbCandle.symbol == symbol,
                DbCandle.timeframe == timeframe
            )
            
            # Apply pagination (historical data)  
            if end_timestamp:
                query = query.where(DbCandle.timestamp < end_timestamp)
                
            # Order and limit
            statement = query.order_by(DbCandle.timestamp.desc()).limit(limit)
            
            results = await session.execute(statement)
            db_candles = results.scalars().all()
            
            # Helper for timeframe ms
            timeframe_ms = {
                '1m': 60 * 1000,
                '5m': 5 * 60 * 1000,
                '15m': 15 * 60 * 1000,
                '30m': 30 * 60 * 1000,
                '1h': 60 * 60 * 1000,
                '4h': 4 * 60 * 60 * 1000,
                '12h': 12 * 60 * 60 * 1000,
                '1d': 24 * 60 * 60 * 1000,
                '3d': 3 * 24 * 60 * 60 * 1000,
                '1w': 7 * 24 * 60 * 60 * 1000,
            }.get(timeframe, 60 * 60 * 1000)

            # Check staleness
            import time
            now_ms = int(time.time() * 1000)
            is_stale = False
            if db_candles and not end_timestamp:
                # db_candles[0] is newest (desc sort)
                latest_ts = db_candles[0].timestamp
                # If latest candle is older than timeframe, we are stale
                # e.g. 1H candle at 10:00 (covers 10-11). Now is 11:05. 
                # Diff = 65 min. timeframe = 60 min. stale.
                if (now_ms - latest_ts) > timeframe_ms:
                    is_stale = True
                    print(f"I: Data stale for {symbol} {timeframe}. Latest: {latest_ts}, Now: {now_ms}")

            # --- Direct Fetch if Missing or Stale ---
            if not db_candles or len(db_candles) < limit // 2 or is_stale:
                print(f"I: Fetching from Binance... (Reason: Missing={not db_candles}, Sparse={len(db_candles) < limit//2 if db_candles else False}, Stale={is_stale})")
                try:
                    provider = BinanceProvider()
                    try:
                        # Calculate 'since' timestamp for fetching older data
                        # If end_timestamp provided, we need to fetch candles BEFORE it
                        # CCXT 'since' = start timestamp, so we go back by limit * timeframe
                        # timeframe_ms map moved up

                        
                        # Calculate 'since' to fetch 1000 candles ending at end_timestamp
                        if end_timestamp:
                            since_ts = end_timestamp - (1000 * timeframe_ms)
                        else:
                            since_ts = None  # Fetch latest
                        
                        print(f"I: Fetching from Binance with since={since_ts}")
                        fresh_candles = await provider.get_ohlcv(symbol, timeframe=timeframe, limit=1000, since=since_ts)
                        
                        # Save to DB
                        for c in fresh_candles:
                            candle_db = CandleModel(
                                symbol=symbol,
                                provider="binance",
                                timeframe=timeframe,
                                timestamp=c.timestamp,
                                open=c.open,
                                high=c.high,
                                low=c.low,
                                close=c.close,
                                volume=c.volume
                            )
                            await session.merge(candle_db)
                        await session.commit()
                        print(f"I: Saved {len(fresh_candles)} candles to DB")
                        
                        # Re-query to get filtered results
                        results = await session.execute(statement)
                        db_candles = results.scalars().all()
                        
                    finally:
                        await provider.close()
                        
                except Exception as e:
                    print(f"E: Failed to fetch from Binance: {e}")
            # ---------------------------

            # Sort ascending for frontend
            db_candles = sorted(db_candles, key=lambda x: x.timestamp)
            
            # Convert to response format
            candles = [
                ProviderCandle(
                    timestamp=c.timestamp,
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume
                ) for c in db_candles
            ]
            
            return OHLCVResponse(
                symbol=symbol,
                timeframe=timeframe,
                provider="postgres-db" if db_candles else "empty",
                candles=candles
            )
    except Exception as e:
        # For MVP, if DB empty/fails, we could fallback to provider? 
        # But per strict architecture, we should just return error or empty.
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


@router.get("/symbols", response_model=List[SymbolInfo])
async def get_symbols():
    """Get list of available trading pairs"""
    provider = get_provider()
    
    try:
        return await provider.get_symbols()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch symbols: {str(e)}")


@router.get("/ticker/{symbol:path}", response_model=TickerResponse)
async def get_ticker(symbol: str):
    """Get current price for a trading pair from Redis Cache or market:tickers"""
    try:
        # Try direct key first
        price = await RedisClient.get_json(f"ticker:{symbol}")
        if price:
            return TickerResponse(symbol=symbol, price=price, provider="cache")
            
        # Fallback: check market:tickers list
        all_tickers = await RedisClient.get_json("market:tickers")
        if all_tickers:
            for ticker in all_tickers:
                if ticker.get('symbol') == symbol:
                    return TickerResponse(symbol=symbol, price=ticker.get('price'), provider="market-cache")
        
        # Still not found - return null price instead of 404
        return TickerResponse(symbol=symbol, price=None, provider="not-found")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticker errors: {str(e)}")


@router.get("/provider")
async def get_provider_info():
    """Get current data provider information"""
    # Simply return generic
    return {"provider": "redis-worker"}


@router.get("/market/summary", response_model=MarketSummaryResponse)
async def get_market_summary():
    """Get market summary statistics from Redis"""
    try:
        data = await RedisClient.get_json("market:tickers")
        if not data:
             return MarketSummaryResponse(total_coins=0, provider="cache-empty")
             
        return MarketSummaryResponse(
            total_coins=len(data),
            provider="redis-cache"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")


async def _get_merged_market_data():
    """
    Merge base market state (CoinGecko Snapshot) with live prices (Binance).
    Returns list of rich ticker dicts.
    """
    # 1. Fetch Snapshot (Base: Rich metadata, 5m old)
    snapshot = await RedisClient.get_json("market:snapshot") or []
    
    # 2. Fetch Live (Overlay: Fast prices, 30s old)
    live_tickers = await RedisClient.get_json("market:tickers") or []
    live_map = {t['symbol']: t for t in live_tickers}
    
    merged = []
    processed_symbols = set()
    
    # 3. Process Snapshot (Base)
    for coin in snapshot:
        symbol = coin.get('symbol')
        if not symbol: continue
        processed_symbols.add(symbol)
        
        # Overlay live data if available
        if symbol in live_map:
            live = live_map[symbol]
            coin['price'] = live.get('price', coin['price'])
            # Only override if live has values
            coin['change_24h'] = live.get('change_24h', coin.get('change_24h'))
            coin['volume_24h'] = live.get('volume_24h', coin.get('volume_24h'))
            coin['high_24h'] = live.get('high_24h')
            coin['low_24h'] = live.get('low_24h')
            # Sparkline comes from snapshot (Base), so it stays
            
        merged.append(coin)
        
    # 4. Add Live Orphans (Tickers in Binance not in CoinGecko snapshot)
    for symbol, live in live_map.items():
        if symbol not in processed_symbols:
            merged.append({
                "symbol": symbol,
                "name": symbol.split('/')[0],
                "price": live.get('price', 0),
                "change_24h": live.get('change_24h', 0),
                "volume_24h": live.get('volume_24h', 0),
                "high_24h": live.get('high_24h', 0),
                "low_24h": live.get('low_24h', 0),
                "market_cap": 0,
                "rank": 9999, # Rank bottom
                "image": None
            })
            
    return merged


@router.get("/market/tickers")
async def get_market_tickers():
    """Get all tickers from merged cache (Base + Live)"""
    try:
        data = await _get_merged_market_data()
        if not data:
             return {"tickers": [], "provider": "cache-empty"}
             
        return {"tickers": data, "provider": "redis-merged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickers: {str(e)}")


@router.get("/market/coins", response_model=CoinsResponse)
async def get_coins(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=10, le=100),
    search: Optional[str] = Query(default=None),
    sort_by: str = Query(default="market_cap", pattern="^(symbol|price|volume_24h|change_24h|market_cap)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$")
):
    """
    Get paginated list of coins from Redis Cache
    """
    try:
        # Fetch fulll merged list
        raw_data = await _get_merged_market_data()
        if not raw_data:
            return CoinsResponse(coins=[], total=0, page=page, page_size=page_size)
            
        # Convert to CoinInfo objects
        coins = []
        for i, t in enumerate(raw_data):
            # t is dict
            coins.append(CoinInfo(
                rank=0, # will resolve later
                symbol=t['symbol'],
                name=t['name'] or t['symbol'].split('/')[0],
                price=t['price'],
                change_24h=t.get('change_24h'),
                volume_24h=t.get('volume_24h'),
                high_24h=t.get('high_24h'),
                low_24h=t.get('low_24h'),
                market_cap=t.get('market_cap') or (t.get('volume_24h', 0) * 15.5), # Heuristic fallback
                image=t.get('image'),
                sparkline_in_7d=t.get('sparkline_in_7d')
            ))
            
        # Filter (Search)
        if search:
            s_upper = search.upper()
            coins = [c for c in coins if s_upper in c.symbol.upper()]
            
        # Sort
        reverse = sort_order == "desc"
        if sort_by == 'price':
            coins.sort(key=lambda x: x.price or 0, reverse=reverse)
        elif sort_by == 'change_24h':
            coins.sort(key=lambda x: x.change_24h or 0, reverse=reverse)
        elif sort_by == 'volume_24h':
            coins.sort(key=lambda x: x.volume_24h or 0, reverse=reverse)
        elif sort_by == 'market_cap':
            coins.sort(key=lambda x: x.market_cap or 0, reverse=reverse)
        else:
            coins.sort(key=lambda x: x.symbol, reverse=reverse)
            
        # Rerank
        for idx, c in enumerate(coins):
            c.rank = idx + 1
            
        # Paginate
        total = len(coins)
        start = (page - 1) * page_size
        end = start + page_size
        page_coins = coins[start:end]
        
        return CoinsResponse(
            coins=page_coins,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch coins: {str(e)}")
