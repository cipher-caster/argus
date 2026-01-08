"""
Liquidation heatmap API routes
"""
import time
from fastapi import APIRouter, Query
from typing import List
from app.storage import RedisClient
from app.schemas.liquidation import (
    LiquidationHeatmapResponse,
    TimeBucket,
    OHLCVPoint,
)

router = APIRouter(prefix="/api/liquidation", tags=["Liquidation"])


@router.get("/heatmap", response_model=LiquidationHeatmapResponse)
async def get_heatmap(
    symbol: str = Query(default="BTCUSDT", description="Trading pair symbol"),
    lookback_hours: int = Query(default=24, ge=1, le=48, description="Hours of data to fetch"),
    bucket_size_seconds: int = Query(default=60, description="Time bucket size in seconds"),
):
    """
    Get liquidation heatmap data for visualization.
    
    Returns time-bucketed price level data with intensity values
    for rendering a heatmap chart.
    """
    redis_key = f"liquidation:{symbol}:buckets"
    raw_data = await RedisClient.get_json(redis_key) or {}
    
    # Filter to lookback window
    cutoff = int(time.time()) - (lookback_hours * 3600)
    filtered = {k: v for k, v in raw_data.items() if int(k) >= cutoff}
    
    # Re-aggregate into requested bucket size (if different from storage bucket)
    # For now, assume storage bucket size matches or is smaller
    time_buckets: List[TimeBucket] = []
    all_prices = set()
    max_volume = 0
    
    for ts_str, price_buckets in sorted(filtered.items()):
        time_buckets.append(TimeBucket(
            timestamp=int(ts_str),
            price_buckets=price_buckets
        ))
        all_prices.update(float(p) for p in price_buckets.keys())
        max_volume = max(max_volume, max(price_buckets.values()) if price_buckets else 0)
    
    # Calculate price range
    if all_prices:
        price_min = min(all_prices)
        price_max = max(all_prices)
    else:
        # Default to current BTC range if no data
        price_min = 90000
        price_max = 100000
    
    # Get OHLCV for candlestick overlay
    # Use cached ticker data from market:tickers
    ohlcv: List[OHLCVPoint] = []
    try:
        tickers = await RedisClient.get_json("market:tickers") or []
        for ticker in tickers:
            if ticker.get("symbol", "").replace("/", "") == symbol:
                # Create a simple "current candle" from ticker
                current_price = ticker.get("price", 0)
                high = ticker.get("high_24h", current_price)
                low = ticker.get("low_24h", current_price)
                ohlcv.append(OHLCVPoint(
                    timestamp=int(time.time()),
                    open=current_price,
                    high=high,
                    low=low,
                    close=current_price
                ))
                break
    except Exception:
        pass  # OHLCV overlay is optional
    
    return LiquidationHeatmapResponse(
        symbol=symbol,
        time_buckets=time_buckets,
        price_min=price_min,
        price_max=price_max,
        max_intensity=max_volume,
        ohlcv=ohlcv,
        bucket_size_seconds=bucket_size_seconds
    )


@router.get("/symbols")
async def get_supported_symbols():
    """Get list of supported symbols for liquidation tracking"""
    # v1: Just BTCUSDT
    return {
        "symbols": ["BTCUSDT"],
        "default": "BTCUSDT"
    }
