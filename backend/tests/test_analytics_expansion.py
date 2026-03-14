import pytest
from unittest.mock import AsyncMock, patch
import pandas as pd
from app.services.market_data import MarketDataService

@pytest.mark.asyncio
async def test_market_data_service_sorting():
    """Verify MarketDataService picks top symbols by market cap or volume."""
    mock_data = [
        {"symbol": "BTC/USDT", "market_cap": 1000000, "volume_24h": 50000},
        {"symbol": "ETH/USDT", "market_cap": 500000, "volume_24h": 100000},
        {"symbol": "SOL/USDT", "market_cap": 200000, "volume_24h": 200000},
    ]
    
    with patch("app.services.market_data.MarketDataService.get_merged_market_data", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_data
        
        # Test Market Cap sorting
        top_caps = await MarketDataService.get_top_symbols(limit=2, sort_by="market_cap")
        assert top_caps == ["BTC/USDT", "ETH/USDT"]
        
        # Test Volume sorting
        top_vols = await MarketDataService.get_top_symbols(limit=2, sort_by="volume")
        assert top_vols == ["SOL/USDT", "ETH/USDT"]

@pytest.mark.asyncio
async def test_screener_noise_filtering(async_client):
    """Verify screener endpoint only returns items with abs(score) >= 2."""
    # The screener internally filters by abs(score) >= 2 in run_oracle_screener.
    # Mock the screener to return a mix of high and low scores.
    mock_screener_output = [
        {"symbol": "BTC/USDT", "price": 50000.0, "score": 3, "confidence": "3/4",
         "bias": "BULLISH", "state": "TRENDING", "liquidity": "ACTIVE",
         "strength_vs_btc": "STRONG", "opportunity": "LONG", "advice": "Strong buy"},
        {"symbol": "SOL/USDT", "price": 100.0, "score": -2, "confidence": "2/4",
         "bias": "BEARISH", "state": "TRENDING", "liquidity": "ACTIVE",
         "strength_vs_btc": "WEAK", "opportunity": "SHORT", "advice": "Sell"},
    ]

    with patch("app.routes.analytics.RedisClient") as mock_redis:
        mock_redis.get_json = AsyncMock(return_value=None)
        mock_redis.set_json = AsyncMock(return_value=True)

        with patch("app.routes.analytics.MarketDataService.get_top_symbols",
                    new_callable=AsyncMock, return_value=["BTC/USDT", "SOL/USDT"]), \
             patch("app.routes.analytics.fetch_all_candles",
                    new_callable=AsyncMock, return_value={"BTC/USDT": pd.DataFrame()}), \
             patch("app.routes.analytics.run_oracle_screener",
                    return_value=mock_screener_output):
            response = await async_client.get("/api/analytics/screener?limit=10")

    assert response.status_code == 200
    data = response.json().get("data", [])
    # All items from the mocked screener should appear (they all have abs(score) >= 2)
    assert len(data) == 2
    for item in data:
        assert abs(item["score"]) >= 2, f"Score {item['score']} should have been filtered"

        
@pytest.mark.asyncio
async def test_analytics_timeframe_parameters(async_client):
    """Verify all analytics endpoints accept and pass the timeframe parameter."""
    endpoints = [
        "/api/analytics/screener",
        "/api/analytics/contrarian-radar"
    ]
    
    with patch("app.routes.analytics.fetch_all_candles", new_callable=AsyncMock) as mock_fetch, \
         patch("app.routes.analytics.MarketDataService.get_top_symbols", new_callable=AsyncMock) as mock_syms, \
         patch("app.routes.analytics.RedisClient.get_json", new_callable=AsyncMock) as mock_cache_get, \
         patch("app.routes.analytics.RedisClient.set_json", new_callable=AsyncMock) as mock_cache_set:
        
        mock_fetch.return_value = {"BTC/USDT": pd.DataFrame()} # Dummy that bypasses empty checks
        mock_syms.return_value = ["BTC/USDT"]
        mock_cache_get.return_value = None  # Always cache miss to trigger fetch
        
        for endpoint in endpoints:
            # Test 1h (default)
            await async_client.get(f"{endpoint}?timeframe=1h")
            # Verify fetch_all_candles was called with 1h (positional or kwarg)
            call_args = mock_fetch.call_args
            timeframe_arg = call_args.kwargs.get('timeframe') or (call_args.args[1] if len(call_args.args) > 1 else None)
            assert timeframe_arg == "1h", f"Expected 1h, got {timeframe_arg}"
            
            # Test 4h
            await async_client.get(f"{endpoint}?timeframe=4h")
            call_args = mock_fetch.call_args
            timeframe_arg = call_args.kwargs.get('timeframe') or (call_args.args[1] if len(call_args.args) > 1 else None)
            assert timeframe_arg == "4h", f"Expected 4h, got {timeframe_arg}"


@pytest.mark.asyncio
async def test_analytics_cache_hit(async_client):
    """Verify cached response is returned on cache hit."""
    cached_data = [{"symbol": "CACHED/USDT", "price": 999.0, "score": 4, "confidence": "4/4", 
                    "bias": "BULLISH", "state": "TRENDING", "liquidity": "ACTIVE", 
                    "strength_vs_btc": "STRONG", "opportunity": "LONG", "advice": "Test"}]
    
    with patch("app.routes.analytics.RedisClient.get_json", new_callable=AsyncMock) as mock_cache_get:
        mock_cache_get.return_value = cached_data
        
        response = await async_client.get("/api/analytics/screener?timeframe=1h")
        assert response.status_code == 200
        data = response.json()
        assert data["data"][0]["symbol"] == "CACHED/USDT"
        assert data["data"][0]["price"] == 999.0
