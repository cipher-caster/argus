"""
Tests for API edge-cases, primarily invalid query parameters.
Ensures the API returns 422 Unprocessable Entity instead of crashing 500.
"""
import pytest
from conftest import mock_cache_miss
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_screener_invalid_timeframe(async_client):
    """Ensure invalid timeframe parameter doesn't cause a 500 error."""
    with patch("app.routes.analytics.RedisClient", mock_cache_miss()), \
         patch("app.routes.analytics.MarketDataService.get_top_symbols", new_callable=AsyncMock, return_value=[]), \
         patch("app.routes.analytics.fetch_all_candles", new_callable=AsyncMock, return_value={}):
        response = await async_client.get("/api/analytics/screener?timeframe=99x")
        # May return 422 (validation error) or 200 (graceful fallback)
        assert response.status_code != 500


@pytest.mark.asyncio
async def test_screener_negative_limit(async_client):
    """Ensure negative limit doesn't cause a 500 error."""
    with patch("app.routes.analytics.RedisClient", mock_cache_miss()), \
         patch("app.routes.analytics.MarketDataService.get_top_symbols", new_callable=AsyncMock, return_value=[]), \
         patch("app.routes.analytics.fetch_all_candles", new_callable=AsyncMock, return_value={}):
        response = await async_client.get("/api/analytics/screener?limit=-5")
        assert response.status_code != 500


@pytest.mark.asyncio
async def test_screener_zero_limit(async_client):
    """Ensure zero limit doesn't cause a 500 error."""
    with patch("app.routes.analytics.RedisClient", mock_cache_miss()), \
         patch("app.routes.analytics.MarketDataService.get_top_symbols", new_callable=AsyncMock, return_value=[]), \
         patch("app.routes.analytics.fetch_all_candles", new_callable=AsyncMock, return_value={}):
        response = await async_client.get("/api/analytics/screener?limit=0")
        assert response.status_code != 500


@pytest.mark.asyncio
async def test_titan_radar_invalid_timeframe(async_client):
    """Ensure invalid timeframe parameter doesn't crash Titan endpoint."""
    with patch("app.routes.analytics.RedisClient", mock_cache_miss()), \
         patch("app.routes.analytics.MarketDataService.get_top_symbols", new_callable=AsyncMock, return_value=[]), \
         patch("app.routes.analytics.fetch_all_candles", new_callable=AsyncMock, return_value={}):
        response = await async_client.get("/api/analytics/titan-radar?timeframe=invalid")
        assert response.status_code != 500


@pytest.mark.asyncio
async def test_best_setups_limit_too_high(async_client):
    """Ensure extremely high limits don't crash."""
    with patch("app.routes.analytics.RedisClient", mock_cache_miss()), \
         patch("app.routes.analytics.MarketDataService.get_top_symbols", new_callable=AsyncMock, return_value=[]), \
         patch("app.routes.analytics.fetch_all_candles", new_callable=AsyncMock, return_value={}):
        response = await async_client.get("/api/analytics/best-setups?limit=1000")
        assert response.status_code != 500


@pytest.mark.asyncio
async def test_market_symbols_invalid_sort(async_client):
    """Ensure imaginary sorts don't crash the symbols route."""
    # Assuming the route exists and is under /api/market/symbols
    with patch("app.routes.market.MarketDataService.get_top_symbols", new_callable=AsyncMock, return_value=[]):
        response = await async_client.get("/api/market/symbols?sort=imaginary_field")
        assert response.status_code != 500
