import pytest
import asyncio
from app.services.liquidation_ws import LiquidationAggregator

@pytest.mark.asyncio
async def test_bucket_calculation():
    """Test price and time bucket calculation logic"""
    agg = LiquidationAggregator("BTCUSDT")
    
    # 1. Test Time Bucket (15s)
    # 10:00:00 (1000ms) -> bucket 66... should be clean div
    # 12345 ms -> 12.345s -> div 15 = 0 -> 0 bucket
    # 16000 ms -> 16s -> div 15 = 1 -> 15 bucket
    assert agg._get_time_bucket(1000) == 0
    assert agg._get_time_bucket(14999) == 0
    assert agg._get_time_bucket(15001) == 15
    
    # 2. Test Price Bucket ($50)
    # Price 99 -> 50
    # Price 49 -> 0
    # Price 101 -> 100
    assert agg._get_price_bucket(49.99) == '0'
    assert agg._get_price_bucket(99.99) == '50'
    assert agg._get_price_bucket(100.01) == '100'
    
    print("Verified: Bucket calculations correct")

@pytest.mark.asyncio
async def test_event_processing():
    """Test that a raw event is correctly processed into a bucket"""
    agg = LiquidationAggregator("BTCUSDT")
    
    # Mock Redis
    from unittest.mock import patch, AsyncMock
    
    # Sample Event: BTCUSDT Long Liquidation: 0.1 BTC @ $50,000
    import time
    now_ts = int(time.time() * 1000)
    event = {
        "o": {
            "s": "BTCUSDT",
            "S": "SELL", # Long liquidated = Sell order
            "q": "0.1",
            "p": "50000",
            "T": now_ts # specific timestamp
        }
    }

    with patch("app.storage.RedisClient.get_json", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {} # Empty existing
        with patch("app.storage.RedisClient.set_json", new_callable=AsyncMock) as mock_set:
            
            await agg._process_event(event)

            # Verification
            assert mock_set.called
            # Check payload structure
            # Key: liquidation:BTCUSDT:buckets
            # Value: { "timestamp_bucket": { "price_bucket": volume } }
            args, _ = mock_set.call_args
            key, payload = args[0], args[1]
            
            assert key == "liquidation:BTCUSDT:buckets"
            
            # Calculate expected bucket dynamically to match implementation
            expected_time = str(agg._get_time_bucket(now_ts))
            expected_price = str(agg._get_price_bucket(50000))
            
            assert payload[expected_time][expected_price] == 5000.0
            print("Verified: Event processed into correct Redis structure")
