"""
Tests for Strategy API Routes (`/api/strategy/*`).
"""
import pytest
from unittest.mock import patch, AsyncMock
import pandas as pd


@pytest.fixture
def mock_db_session():
    # Helper to create a mock async db session that returns empty or mock rows
    session = AsyncMock()
    # By default, mock returning no DB candles
    session.execute.return_value.scalars.return_value.all.return_value = []
    return session


@pytest.mark.asyncio
async def test_get_oracle_strategy_success(async_client, mock_db_session):
    """Test the /oracle route returns Oracle response correctly."""
    
    # Mock get_candles_df to bypass DB/Binance logic and just return mock OHLCV
    mock_df_micro = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10, freq="1h"),
        "open": [10]*10, "high": [11]*10, "low": [9]*10, "close": [10.5]*10, "volume": [1000]*10
    })
    mock_df_macro = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10, freq="1d"),
        "open": [10]*10, "high": [11]*10, "low": [9]*10, "close": [10.5]*10, "volume": [1000]*10
    })

    # The route calls get_candles_df twice (micro and macro)
    with patch("app.routes.strategy.RedisClient.get_json", new_callable=AsyncMock, return_value=None):
        with patch("app.routes.strategy.RedisClient.set_json", new_callable=AsyncMock):
            with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, side_effect=[mock_df_micro, mock_df_macro]):
                with patch("app.routes.strategy.oracle.analyze") as mock_analyze:
                    # Mock the oracle analysis response
                    mock_analyze.return_value = {"signal": "BUY", "confidence": "2/4"}

                    response = await async_client.get("/api/strategy/oracle/BTCUSDT?micro_tf=1h&macro_tf=1d")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["signal"] == "BUY"
                    assert data["symbol"] == "BTCUSDT"
                    assert data["micro_tf"] == "1h"
                    assert data["price"] == 10.5


@pytest.mark.asyncio
async def test_get_oracle_strategy_insufficient_data(async_client):
    """Test poor data returns 404."""
    with patch("app.routes.strategy.RedisClient.get_json", new_callable=AsyncMock, return_value=None):
        with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=pd.DataFrame()):
            response = await async_client.get("/api/strategy/oracle/BTCUSDT")
            assert response.status_code == 404
            assert "Insufficient data" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_titan_strategy_success(async_client):
    """Test the /titan route returns Titan response."""
    mock_df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=250, freq="4h"),
        "open": [10]*250, "high": [11]*250, "low": [9]*250, "close": [10.5]*250, "volume": [1000]*250
    })

    with patch("app.routes.strategy.RedisClient.get_json", new_callable=AsyncMock, return_value=None):
        with patch("app.routes.strategy.RedisClient.set_json", new_callable=AsyncMock):
            with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=mock_df):
                with patch("app.routes.strategy.titan.analyze") as mock_analyze:
                    mock_analyze.return_value = {"signal": "BUY", "confidence": 80}

                    response = await async_client.get("/api/strategy/titan/ETHUSDT?timeframe=4h")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["signal"] == "BUY"
                    assert data["symbol"] == "ETHUSDT"
                    assert data["timeframe"] == "4h"
                    assert data["price"] == 10.5

@pytest.mark.asyncio
async def test_get_titan_strategy_insufficient_data(async_client):
    """Test titan route handles empty data."""
    with patch("app.routes.strategy.RedisClient.get_json", new_callable=AsyncMock, return_value=None):
        with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=pd.DataFrame()):
            response = await async_client.get("/api/strategy/titan/SOLUSDT")
            assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_candles_df_binance_fallback():
    """Test the internal helper `get_candles_df` directly to ensure DB/Binance logic works."""
    from app.routes.strategy import get_candles_df
    
    # SQLAlchemy session setup
    from unittest.mock import MagicMock
    
    # The return of execute() is a synchronous result object
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    
    # The session itself has an async execute() method
    session_mock = AsyncMock()
    session_mock.execute.return_value = result_mock
    
    # get_session is an async context manager
    db_mock = AsyncMock()
    db_mock.__aenter__.return_value = session_mock

    
    class FakeCandle:
        def __init__(self, ts):
            self.timestamp = ts
            self.open = 10.0
            self.high = 11.0
            self.low = 9.0
            self.close = 10.5
            self.volume = 1000.0

    mock_fresh = [FakeCandle(1000), FakeCandle(2000)]
    
    binance_provider_mock = AsyncMock()
    binance_provider_mock.get_ohlcv.return_value = mock_fresh
    
    with patch("app.routes.strategy.Database.get_session", return_value=db_mock):
        df = await get_candles_df("AAVEUSDT", "1h", limit=50, provider=binance_provider_mock)
    
    assert not df.empty
    assert len(df) == 2
    assert "timestamp" in df.columns
    assert df.iloc[-1]["close"] == 10.5
    # Ensure Binance provider was called since DB was empty
    binance_provider_mock.get_ohlcv.assert_called_once()


@pytest.mark.asyncio
async def test_oracle_strategy_generic_500_on_unexpected_error(async_client):
    """When an unexpected exception occurs, the API returns 500 with a generic message (no raw str(e))."""
    with patch("app.routes.strategy.RedisClient.get_json", new_callable=AsyncMock, return_value=None):
        with patch(
            "app.routes.strategy.get_candles_df",
            new_callable=AsyncMock,
            side_effect=RuntimeError("internal details that should not leak"),
        ):
            response = await async_client.get("/api/strategy/oracle/BTCUSDT")
            assert response.status_code == 500
            detail = response.json()["detail"]
            assert detail == "Internal server error"
            assert "internal details that should not leak" not in detail


@pytest.mark.asyncio
async def test_titan_strategy_generic_500_on_unexpected_error(async_client):
    """When an unexpected exception occurs, the titan route returns 500 with a generic message."""
    with patch("app.routes.strategy.RedisClient.get_json", new_callable=AsyncMock, return_value=None):
        with patch(
            "app.routes.strategy.get_candles_df",
            new_callable=AsyncMock,
            side_effect=RuntimeError("sensitive internal detail"),
        ):
            response = await async_client.get("/api/strategy/titan/BTCUSDT")
            assert response.status_code == 500
            detail = response.json()["detail"]
            assert detail == "Internal server error"
            assert "sensitive internal detail" not in detail
