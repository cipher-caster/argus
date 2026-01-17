import pytest
import pandas as pd
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_trend_radar_endpoint(async_client):
    """Verify Trend Radar endpoint returns correctly categorized structure."""
    
    mock_result = {
        "map": [
            {
                "symbol": "BTC/USDT",
                "price": 50000.0,
                "ema200": 49000.0,
                "distance_pct": 2.0,
                "status": "BULLISH",
                "volume": 1000000.0
            }
        ],
        "buckets": {
            "BULLISH": ["BTC/USDT"],
            "BEARISH": []
        },
        "summary": {
            "BULLISH": 1,
            "BEARISH": 0
        }
    }
    
    with patch("app.routes.analytics.fetch_all_candles", new_callable=AsyncMock) as mock_fetch, \
         patch("app.routes.analytics.MarketDataService.get_top_symbols", new_callable=AsyncMock) as mock_syms, \
         patch("app.routes.analytics.RedisClient.get_json", new_callable=AsyncMock) as mock_cache_get, \
         patch("app.routes.analytics.RedisClient.set_json", new_callable=AsyncMock), \
         patch("app.indicators.trend_radar.TrendRadar.analyze") as mock_analyze:
        
        mock_cache_get.return_value = None
        mock_syms.return_value = ["BTC/USDT"]
        mock_fetch.return_value = {"BTC/USDT": pd.DataFrame()}
        mock_analyze.return_value = mock_result
        
        response = await async_client.get("/api/analytics/trend-radar?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "map" in data
        assert data["map"][0]["symbol"] == "BTC/USDT"
        assert data["summary"]["BULLISH"] == 1

@pytest.mark.asyncio
async def test_structure_scanner_endpoint(async_client):
    """Verify Structure Scanner endpoint."""
    
    mock_data = [
        {
            "symbol": "ETH/USDT", 
            "price": 1950.0,
            "monday_high": 2000.0, 
            "monday_low": 1900.0, 
            "status": "INSIDE_RANGE",
            "range_pct": 5.0
        }
    ]
    
    with patch("app.routes.analytics.fetch_all_candles", new_callable=AsyncMock) as mock_fetch, \
         patch("app.routes.analytics.MarketDataService.get_top_symbols", new_callable=AsyncMock) as mock_syms, \
         patch("app.routes.analytics.RedisClient.get_json", new_callable=AsyncMock) as mock_cache_get, \
         patch("app.routes.analytics.RedisClient.set_json", new_callable=AsyncMock), \
         patch("app.indicators.structure.StructureScanner.analyze") as mock_analyze:
        
        mock_cache_get.return_value = None
        mock_syms.return_value = ["ETH/USDT"]
        mock_fetch.return_value = {"ETH/USDT": pd.DataFrame()}
        mock_analyze.return_value = mock_data
        
        response = await async_client.get("/api/analytics/structure?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["symbol"] == "ETH/USDT"
        assert data["data"][0]["status"] == "INSIDE_RANGE"

@pytest.mark.asyncio
async def test_confluence_endpoint(async_client):
    """Verify Confluence endpoint aggregates screener data."""
    
    mock_screener_data = [
        {"symbol": "BTC/USDT", "score": 4},
        {"symbol": "ETH/USDT", "score": 4},
        {"symbol": "SOL/USDT", "score": -1}
    ]
    
    mock_analysis = {
        "verdict": "TSUNAMI_BULL",
        "metrics": {
            "total_analyzed": 3,
            "sleeping_pct": 0.0,
            "bullish_pct": 66.7,
            "bearish_pct": 33.3
        },
        "score_distribution": {"4": 2, "-1": 1}
    }
    
    # Test path where screener data is in Redis
    with patch("app.routes.analytics.RedisClient.get_json", new_callable=AsyncMock) as mock_cache_get, \
         patch("app.routes.analytics.RedisClient.set_json", new_callable=AsyncMock), \
         patch("app.indicators.confluence.ConfluenceAggregator.analyze") as mock_analyze:
         
        mock_cache_get.return_value = mock_screener_data
        mock_analyze.return_value = mock_analysis
        
        response = await async_client.get("/api/analytics/confluence?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["verdict"] == "TSUNAMI_BULL"
        assert data["metrics"]["total_analyzed"] == 3

@pytest.mark.asyncio
async def test_signal_summary_endpoint(async_client):
    """Verify Signal Summary endpoint logic."""
    
    mock_screener = [
        {"symbol": "A", "score": 4}, # Bull
        {"symbol": "B", "score": 3}, # Bull
        {"symbol": "C", "score": -3}, # Bear
        {"symbol": "D", "score": 0}, # Neutral
    ]
    # 2 Bulls, 1 Bear, 1 Neutral. Total 4.
    # Bullish Pct = 50%, Bearish Pct = 25%
    
    with patch("app.routes.analytics.fetch_all_candles", new_callable=AsyncMock), \
         patch("app.routes.analytics.MarketDataService.get_top_symbols", new_callable=AsyncMock), \
         patch("app.routes.analytics.run_oracle_screener") as mock_run, \
         patch("app.routes.analytics.calculate_market_health") as mock_health, \
         patch("app.routes.analytics.ConfluenceAggregator.analyze") as mock_conf, \
         patch("app.routes.analytics.RedisClient.get_json", new_callable=AsyncMock) as mock_get, \
         patch("app.routes.analytics.RedisClient.set_json", new_callable=AsyncMock):
         
         mock_get.return_value = None
         mock_run.return_value = mock_screener
         mock_health.return_value = {}
         mock_conf.return_value = {"verdict": "CHOP"}
         
         response = await async_client.get("/api/analytics/signal-summary")
         assert response.status_code == 200
         data = response.json()
         
         assert data["bullish_pct"] == 50.0
         assert data["bearish_pct"] == 25.0
         assert data["market_state"] == "NEUTRAL" # CHOP -> NEUTRAL
         assert "A 4/4" in data["top_signals"]
