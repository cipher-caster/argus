"""
Tests for background worker jobs (`worker.py`).
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.worker import sync_market_summary, sync_market_snapshot, sync_analytics_cache


@pytest.fixture
def mock_ctx():
    """Provides a mock worker context dictionary with a mock Binance provider."""
    provider_mock = AsyncMock()
    return {'provider': provider_mock}


@pytest.mark.asyncio
async def test_sync_market_summary_success(mock_ctx):
    """Test that sync_market_summary successfully fetches tickers and caches them."""
    # Mock return data matching Binance format
    mock_ctx['provider'].get_all_tickers.return_value = {
        "BTC/USDT": {"last": 50000.0, "percentage": 5.0, "quoteVolume": 1000000.0, "high": 51000.0, "low": 49000.0},
        "ETH/USDT": {"last": 3000.0, "percentage": -2.0, "quoteVolume": 500000.0, "high": 3100.0, "low": 2900.0},
        "DOGE/BTC": {"last": 0.00001, "percentage": 1.0, "quoteVolume": 100.0} # Should be ignored (not USDT)
    }

    mock_provider = mock_ctx['provider']
    mock_provider.name = "binance"

    with patch("app.worker.get_active_provider", new_callable=AsyncMock, return_value=mock_provider):
        with patch("app.worker.RedisClient.set_json", new_callable=AsyncMock) as mock_set_json:
            with patch("app.worker.RedisClient.get_instance"):
                await sync_market_summary(mock_ctx)

            # Should be called twice (once for summary, once for tickers)
            assert mock_set_json.call_count == 2

            # Verify the tickers list cache
            tickers_call_args = mock_set_json.call_args_list[1][0]
            assert tickers_call_args[0] == "market:tickers"
            tickers_data = tickers_call_args[1]
            assert len(tickers_data) == 2 # Only USDT pairs


@pytest.mark.asyncio
async def test_sync_market_summary_handles_provider_error(mock_ctx):
    """Test that the job gracefully handles errors from the provider."""
    mock_provider = AsyncMock()
    mock_provider.name = "binance"
    mock_provider.get_all_tickers.side_effect = Exception("Binance API down")

    # Should not raise an exception or crash the worker
    with patch("app.worker.get_active_provider", new_callable=AsyncMock, return_value=mock_provider):
        with patch("app.worker.logger.error") as mock_logger:
            await sync_market_summary(mock_ctx)
            mock_logger.assert_called_once()
            assert "Job Failed: sync_market_summary" in mock_logger.call_args[0][0]


@pytest.mark.asyncio
async def test_sync_market_snapshot_success():
    """Test the CoinGecko snapshot fetcher handles pagination and transforms correctly."""
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "symbol": "btc",
            "current_price": 50000,
            "price_change_percentage_1h_in_currency": 0.5,
            "price_change_percentage_24h": -1.0,
            "price_change_percentage_7d_in_currency": 5.0,
            "total_volume": 1000000,
            "market_cap": 900000000,
            "market_cap_rank": 1,
            "image": "btc.png",
            "name": "Bitcoin",
            "sparkline_in_7d": {"price": [49000, 49500, 50000]}
        }
    ]
    
    class MockClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        async def get(self, *args, **kwargs):
            return mock_response
            
    with patch("httpx.AsyncClient", return_value=MockClient()):
        with patch("app.worker.RedisClient.set_json", new_callable=AsyncMock) as mock_set_json:
            # We also need to mock asyncio.sleep so we don't wait 1s during the test
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await sync_market_snapshot({})
                
                mock_set_json.assert_called_once()
                args = mock_set_json.call_args[0]
                assert args[0] == "market:snapshot"
                
                snapshot_data = args[1]
                assert len(snapshot_data) == 1
                assert snapshot_data[0]["symbol"] == "BTC/USDT"
                assert snapshot_data[0]["price"] == 50000
