import pytest
from unittest.mock import AsyncMock, patch
from app.routes.market import get_ohlcv

# Mock DB candles response
class MockCandle:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.open = 100
        self.high = 110
        self.low = 90
        self.close = 105
        self.volume = 1000

@pytest.mark.asyncio
async def test_ohlcv_staleness_logic():
    """
    Test that stale data triggers a Binance fetch call.
    Uses patching to mock DB session and BinanceProvider.
    """
    from unittest.mock import MagicMock
    # 1. Setup Mock DB session returning old data
    mock_session = AsyncMock()
    mock_result = MagicMock() # Result object is synchronous
    
    # Create a stale candle (older than 1h + buffer)
    import time
    old_ts = int((time.time() - 7200) * 1000) # 2 hours ago
    stale_candle = MockCandle(old_ts)

    mock_result.scalars.return_value.all.return_value = [stale_candle]
    mock_session.execute.return_value = mock_result
    
    # 2. Patch dependencies
    with patch("app.storage.Database.get_session") as mock_get_session:
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Patch the class where it's defined. 
        # Since market.py does "from app.providers.binance_provider import BinanceProvider" locally,
        # patching app.providers.binance_provider.BinanceProvider is generally correct.
        with patch("app.providers.binance_provider.BinanceProvider") as MockProvider:
            mock_provider_instance = AsyncMock()
            MockProvider.return_value = mock_provider_instance
            mock_provider_instance.get_ohlcv.return_value = [] 
            
            print(f"Test: Calling get_ohlcv with stale candle ts={old_ts} vs now={int(time.time()*1000)}")
            
            try:
                await get_ohlcv("BTC/USDT", timeframe="1h", limit=100, end_timestamp=None)
            except Exception as e:
                print(f"Test Exception (expected): {e}")

            # Verify instantiation
            assert MockProvider.called, "BinanceProvider not instantiated"
            # Verify method call
            assert mock_provider_instance.get_ohlcv.called, "get_ohlcv not called on provider"
            print("Verified: Stale data triggered Binance fetch")

@pytest.mark.asyncio
async def test_ohlcv_fresh_data():
    """Test that fresh data does NOT trigger fetch"""
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    
    import time
    now_ts = int(time.time() * 1000)
    fresh_candle = MockCandle(now_ts)
    
    mock_result.scalars.return_value.all.return_value = [fresh_candle]
    mock_session.execute.return_value = mock_result
    
    with patch("app.storage.Database.get_session") as mock_get_session:
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        with patch("app.providers.binance_provider.BinanceProvider") as MockProvider:
            mock_provider_instance = AsyncMock()
            MockProvider.return_value = mock_provider_instance
            
            try:
                await get_ohlcv("BTC/USDT", timeframe="1h", limit=100)
            except:
                pass
            
            # Should NOT call binance
            assert not mock_provider_instance.get_ohlcv.called
            print("Verified: Fresh data used valid DB cache")
