"""
Market Data API Routes
Endpoints for fetching OHLCV data and symbol information
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.providers import Candle, SymbolInfo


router = APIRouter(prefix="/api", tags=["market"])


class OHLCVResponse(BaseModel):
    """Response model for OHLCV endpoint"""
    symbol: str
    timeframe: str
    provider: str
    candles: List[Candle]


class TickerResponse(BaseModel):
    """Response model for ticker price"""
    symbol: str
    price: Optional[float]
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
    timeframe: str = Query(default="1h", pattern="^(1m|5m|15m|30m|1h|4h|1d|1w)$"),
    limit: int = Query(default=100, ge=1, le=500)
):
    """
    Fetch OHLCV candlestick data for a trading pair
    
    - **symbol**: Trading pair (e.g., BTC/USDT)
    - **timeframe**: Candle timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
    - **limit**: Number of candles (1-500)
    """
    provider = get_provider()
    
    try:
        candles = await provider.get_ohlcv(symbol, timeframe, limit)
        return OHLCVResponse(
            symbol=symbol,
            timeframe=timeframe,
            provider=provider.name,
            candles=candles
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch data: {str(e)}")


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
    """Get current price for a trading pair"""
    provider = get_provider()
    
    try:
        price = await provider.get_ticker_price(symbol)
        return TickerResponse(
            symbol=symbol,
            price=price,
            provider=provider.name
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch ticker: {str(e)}")


@router.get("/provider")
async def get_provider_info():
    """Get current data provider information"""
    provider = get_provider()
    return {"provider": provider.name}


class CoinInfo(BaseModel):
    """Coin information for table display"""
    rank: int
    symbol: str
    name: str
    price: float
    change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None


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


@router.get("/market/summary", response_model=MarketSummaryResponse)
async def get_market_summary():
    """Get market summary statistics"""
    provider = get_provider()
    
    try:
        symbols = await provider.get_symbols()
        return MarketSummaryResponse(
            total_coins=len(symbols),
            provider=provider.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")


@router.get("/market/coins", response_model=CoinsResponse)
async def get_coins(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=10, le=100),
    search: Optional[str] = Query(default=None),
    sort_by: str = Query(default="symbol", pattern="^(symbol|price|volume_24h|change_24h)$"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$")
):
    """
    Get paginated list of coins with prices
    
    - **page**: Page number (1-indexed)
    - **page_size**: Items per page (10-100)
    - **search**: Filter by symbol name
    - **sort_by**: Sort field (symbol, price, volume_24h, change_24h)
    - **sort_order**: Sort direction (asc, desc)
    """
    provider = get_provider()
    
    try:
        # Get all symbols
        symbols = await provider.get_symbols()
        
        # Filter by search term
        if search:
            search_upper = search.upper()
            symbols = [s for s in symbols if search_upper in s.symbol.upper()]
        
        # Batch fetch all tickers at once
        all_tickers = await provider.get_all_tickers()
        
        # Build coins list with prices
        coins = []
        for idx, sym in enumerate(symbols):
            ticker = all_tickers.get(sym.symbol)
            if ticker:  # Only include coins with valid ticker data
                price = ticker.get('last')
                if price:
                    coins.append(CoinInfo(
                        rank=idx + 1,
                        symbol=sym.symbol,
                        name=sym.symbol.replace("/USDT", "").replace("/USD", ""),
                        price=price,
                        change_24h=ticker.get('percentage'),
                        volume_24h=ticker.get('quoteVolume'),
                        high_24h=ticker.get('high'),
                        low_24h=ticker.get('low')
                    ))
        
        # Sort
        reverse = sort_order == "desc"
        if sort_by == "price":
            coins.sort(key=lambda c: c.price, reverse=reverse)
        elif sort_by == "volume_24h":
            coins.sort(key=lambda c: c.volume_24h or 0, reverse=reverse)
        elif sort_by == "change_24h":
            coins.sort(key=lambda c: c.change_24h or 0, reverse=reverse)
        else:
            coins.sort(key=lambda c: c.symbol, reverse=reverse)
        
        # Update ranks after sorting
        for idx, coin in enumerate(coins):
            coin.rank = idx + 1
        
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
