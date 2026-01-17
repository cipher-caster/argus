import pytest
import asyncio
from unittest.mock import MagicMock, patch
from app.routes.market import _get_merged_market_data

@pytest.mark.asyncio
async def test_market_merge_logic():
    """
    Test that _get_merged_market_data correctly merges:
    1. CoinGecko Snapshot (Base)
    2. Binance Live Tickers (Overlay)
    """
    
    # 1. Mock Data: Snapshot (Base State)
    mock_snapshot = [
        {
            "symbol": "BTC/USDT",
            "name": "Bitcoin", 
            "price": 50000.0,
            "change_24h": 1.0,
            "volume_24h": 100000,
            "market_cap": 1000000000,
            "image": "btc.png",
            "sparkline_in_7d": [50000, 50100, 50200]
        },
        {
            "symbol": "PEPE/USDT", # Only in Snapshot
            "name": "Pepe",
            "price": 0.00001,
            "change_24h": -5.0,
            "sparkline_in_7d": [1, 2, 3]
        }
    ]
    
    # 2. Mock Data: Live (Updates)
    mock_live = [
        {
            "symbol": "BTC/USDT",
            "price": 50500.0, # NEW PRICE
            "change_24h": 2.0, # NEW CHANGE
            "volume_24h": 200000,
            "high_24h": 51000,
            "low_24h": 49000
        },
        {
            "symbol": "SOL/USDT", # Orphan (Only in Live)
            "price": 100.0,
            "change_24h": 5.0,
            "volume_24h": 5000
        }
    ]
    
    # 3. Patch RedisClient.get_json to return our mocks
    # First call returns snapshot, second call returns live
    with patch("app.storage.RedisClient.get_json", side_effect=[mock_snapshot, mock_live]):
        
        # Execute
        merged = await _get_merged_market_data()
        
        # --- VERIFICATION ---
        
        # Should have 3 items: BTC (merged), PEPE (snapshot only), SOL (live orphan)
        assert len(merged) == 3
        
        # 1. Check BTC Merger
        btc = next(item for item in merged if item["symbol"] == "BTC/USDT")
        assert btc["price"] == 50500.0, "Should use LIVE price"
        assert btc["change_24h"] == 2.0, "Should use LIVE change"
        assert btc["image"] == "btc.png", "Should keep SNAPSHOT image"
        assert btc["sparkline_in_7d"] == [50000, 50100, 50200], "Should keep SNAPSHOT sparkline"
        
        # 2. Check PEPE Preservation
        pepe = next(item for item in merged if item["symbol"] == "PEPE/USDT")
        assert pepe["price"] == 0.00001, "Should use SNAPSHOT price when no live data"
        
        # 3. Check SOL Addition
        sol = next(item for item in merged if item["symbol"] == "SOL/USDT")
        assert sol["price"] == 100.0, "Should include pure LIVE coins"
        assert sol["name"] == "SOL", "Should derive name from symbol"
        assert sol["image"] is None, "Live-only coins lack images"

        assert sol["image"] is None, "Live-only coins lack images"


@pytest.mark.asyncio
async def test_market_sorting():
    """Test API sorting logic"""
    from app.routes.market import get_coins
    
    # Mock Merged Data
    mock_data = [
        {"symbol": "A", "name": "A", "price": 10.0, "volume_24h": 100.0, "market_cap": 1000.0, "change_24h": 0},
        {"symbol": "B", "name": "B", "price": 5.0, "volume_24h": 500.0, "market_cap": 500.0, "change_24h": 0},
        {"symbol": "C", "name": "C", "price": 20.0, "volume_24h": 50.0, "market_cap": 2000.0, "change_24h": 0},
    ]
    
    with patch("app.routes.market._get_merged_market_data", new_callable=MagicMock) as mock_get:
        # Since _get_merged_market_data is awaited, the mock return value needs to be awaitable or the function mocked properly
        # Simpler: mock the return value as a future
        f = asyncio.Future()
        f.set_result(mock_data)
        mock_get.return_value = f
        
        # 1. Price Sort (Desc) -> C (20), A (10), B (5)
        resp = await get_coins(page=1, page_size=50, search=None, sort_by="price", sort_order="desc")
        assert resp.coins[0].symbol == "C"
        assert resp.coins[1].symbol == "A"
        assert resp.coins[2].symbol == "B"
        
        # 2. Volume Sort (Desc) -> B (500), A (100), C (50)
        # We need to recreate the mock return or just call again (return_value is static mock)
        resp = await get_coins(page=1, page_size=50, search=None, sort_by="volume_24h", sort_order="desc")
        assert resp.coins[0].symbol == "B"
        
         # 3. Market Cap Sort (Desc) -> C (2000), A (1000), B (500)
        resp = await get_coins(page=1, page_size=50, search=None, sort_by="market_cap", sort_order="desc")
        assert resp.coins[0].symbol == "C"
