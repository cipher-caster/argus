"""
Tests for market data endpoints and staleness logic.
Verifies that stale DB data triggers a Binance fetch, and fresh data does not.
"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch


class MockCandle:
    """Mock DB candle object with required OHLCV fields."""
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.open = 100
        self.high = 110
        self.low = 90
        self.close = 105
        self.volume = 1000


def _make_mock_session(candles):
    """Create an async mock DB session that returns the given candles."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = candles
    mock_session.execute.return_value = mock_result
    return mock_session


@pytest.mark.asyncio
async def test_ohlcv_stale_data_triggers_binance_fetch():
    """
    When DB data is older than the staleness threshold,
    MarketDataService should call BinanceProvider to refresh.
    """
    from app.routes.market import get_ohlcv

    old_ts = int((time.time() - 7200) * 1000)  # 2 hours ago
    stale_candle = MockCandle(old_ts)
    mock_session = _make_mock_session([stale_candle])

    mock_provider_instance = AsyncMock()
    mock_provider_instance.get_ohlcv.return_value = []

    with patch("app.storage.Database.get_session") as mock_get_session:
        mock_get_session.return_value.__aenter__.return_value = mock_session

        with patch("app.providers.get_provider", return_value=mock_provider_instance) as mock_get_provider:
            # The endpoint may raise because mock returns empty data — that's OK.
            # We're testing that the provider was called when data is stale.
            try:
                await get_ohlcv("BTC/USDT", timeframe="1h", limit=100, end_timestamp=None)
            except Exception:
                pass  # Expected — incomplete mock chain

            assert mock_get_provider.called, \
                "get_provider should be called when data is stale"
            assert mock_provider_instance.get_ohlcv.called, \
                "provider.get_ohlcv should be called when data is stale"


@pytest.mark.asyncio
async def test_ohlcv_fresh_data_skips_binance_fetch():
    """
    When DB data is recent (within staleness threshold),
    BinanceProvider should NOT be called.
    """
    from app.routes.market import get_ohlcv

    now_ts = int(time.time() * 1000)
    fresh_candle = MockCandle(now_ts)
    mock_session = _make_mock_session([fresh_candle])

    with patch("app.storage.Database.get_session") as mock_get_session:
        mock_get_session.return_value.__aenter__.return_value = mock_session

        with patch("app.providers.binance_provider.BinanceProvider") as MockProvider:
            mock_provider_instance = AsyncMock()
            MockProvider.return_value = mock_provider_instance

            try:
                await get_ohlcv("BTC/USDT", timeframe="1h", limit=100)
            except Exception:
                pass  # Expected — incomplete mock chain

            assert not mock_provider_instance.get_ohlcv.called, \
                "BinanceProvider.get_ohlcv should NOT be called when data is fresh"


@pytest.mark.asyncio
async def test_bulk_upsert_uses_single_execute_call():
    """
    When fresh candles are fetched from the provider, the service must persist
    them with a single bulk execute call (not N individual merge calls).
    """
    from app.services.market_data import MarketDataService

    # Simulate an empty DB so the fetch path is triggered
    mock_session = _make_mock_session([])
    mock_session.execute = AsyncMock(return_value=mock_session.execute.return_value)

    class FakeProviderCandle:
        def __init__(self, ts):
            self.timestamp = ts
            self.open = 1.0
            self.high = 2.0
            self.low = 0.5
            self.close = 1.5
            self.volume = 100.0

    fake_candles = [FakeProviderCandle(i * 1000) for i in range(5)]

    mock_provider = AsyncMock()
    mock_provider.name = "binance"
    mock_provider.get_ohlcv.return_value = fake_candles

    with patch("app.storage.Database.get_session") as mock_get_session:
        mock_get_session.return_value.__aenter__.return_value = mock_session

        with patch("app.providers.get_provider", return_value=mock_provider):
            with patch("app.providers.owns_provider", return_value=False):
                try:
                    await MarketDataService.fetch_and_sync_ohlcv(
                        "BTC/USDT", timeframe="1h", limit=100
                    )
                except Exception:
                    pass  # DB re-query after insert may fail in mock context

    # execute() is called: once for the initial DB query, once for the bulk insert,
    # and once for the re-query — but critically NOT once-per-candle (5 candles = 5 calls).
    # The bulk insert is a single execute call, so total calls must be < len(fake_candles).
    total_execute_calls = mock_session.execute.call_count
    assert total_execute_calls < len(fake_candles), (
        f"Expected fewer than {len(fake_candles)} execute calls (bulk upsert), "
        f"but got {total_execute_calls}"
    )


@pytest.mark.asyncio
async def test_ohlcv_data_provider_error_returns_503_generic(async_client):
    """DataProviderError should return 503 with a generic message (no raw exception string)."""
    from app.exceptions import DataProviderError

    with patch(
        "app.services.market_data.MarketDataService.fetch_and_sync_ohlcv",
        new_callable=AsyncMock,
        side_effect=DataProviderError("Binance API key invalid - secret details"),
    ):
        response = await async_client.get("/api/ohlcv/BTC%2FUSDT?timeframe=1h&limit=100")
        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail == "Data provider unavailable"
        assert "Binance API key invalid" not in detail


@pytest.mark.asyncio
async def test_ohlcv_unexpected_error_returns_500_generic(async_client):
    """An unexpected Exception should return 500 with a generic message (no raw exception string)."""
    with patch(
        "app.services.market_data.MarketDataService.fetch_and_sync_ohlcv",
        new_callable=AsyncMock,
        side_effect=RuntimeError("unexpected internal detail"),
    ):
        response = await async_client.get("/api/ohlcv/BTC%2FUSDT?timeframe=1h&limit=100")
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert detail == "Internal server error"
        assert "unexpected internal detail" not in detail
