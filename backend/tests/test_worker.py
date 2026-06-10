"""
Tests for background worker jobs (`worker.py`).
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.worker import (
    _retry,
    backfill_okx_candles,
    execute_signals,
    sync_market_snapshot,
    sync_market_summary,
)


@pytest.fixture
def mock_ctx():
    """Provides a mock worker context dictionary with a mock Binance provider."""
    provider_mock = AsyncMock()
    return {"provider": provider_mock}


@pytest.mark.asyncio
async def test_sync_market_summary_success(mock_ctx):
    """Test that sync_market_summary successfully fetches tickers and caches them."""
    # Mock return data matching Binance format
    mock_ctx["provider"].get_all_tickers.return_value = {
        "BTC/USDT": {
            "last": 50000.0,
            "percentage": 5.0,
            "quoteVolume": 1000000.0,
            "high": 51000.0,
            "low": 49000.0,
        },
        "ETH/USDT": {
            "last": 3000.0,
            "percentage": -2.0,
            "quoteVolume": 500000.0,
            "high": 3100.0,
            "low": 2900.0,
        },
        "DOGE/BTC": {
            "last": 0.00001,
            "percentage": 1.0,
            "quoteVolume": 100.0,
        },  # Should be ignored (not USDT)
    }

    mock_provider = mock_ctx["provider"]
    mock_provider.name = "okx"

    with patch(
        "app.worker.get_active_provider", new_callable=AsyncMock, return_value=mock_provider
    ):
        with patch("app.worker.RedisClient.set_json", new_callable=AsyncMock) as mock_set_json:
            with patch("app.worker.RedisClient.get_instance"):
                await sync_market_summary(mock_ctx)

            # Should be called twice (once for summary, once for tickers)
            assert mock_set_json.call_count == 2

            # Verify the tickers list cache
            tickers_call_args = mock_set_json.call_args_list[1][0]
            assert tickers_call_args[0] == "market:tickers"
            tickers_data = tickers_call_args[1]
            assert len(tickers_data) == 2  # Only USDT pairs


@pytest.mark.asyncio
async def test_sync_market_summary_handles_provider_error(mock_ctx):
    """Test that the job gracefully handles errors from the provider after all retries."""
    mock_provider = AsyncMock()
    mock_provider.name = "okx"
    mock_provider.get_all_tickers.side_effect = Exception("OKX API down")

    # Should not raise an exception or crash the worker
    # New behavior: sets backoff and returns early (no Binance fallback)
    with patch(
        "app.worker.get_active_provider", new_callable=AsyncMock, return_value=mock_provider
    ):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with patch("app.worker.logger.warning") as mock_logger:
                await sync_market_summary(mock_ctx)
                # After all retries fail, logs a warning and enters backoff
                assert mock_logger.called


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
            "sparkline_in_7d": {"price": [49000, 49500, 50000]},
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


# --- Tests for _retry helper ---


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt():
    """_retry should return the result when a callable fails once then succeeds."""
    call_count = 0

    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("transient error")
        return "ok"

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await _retry(flaky, retries=3, delay=0.0, label="test")

    assert result == "ok"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_raises_after_max_retries():
    """_retry should raise the exception after exhausting all retry attempts."""
    call_count = 0

    async def always_fails():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("network down")

    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(ConnectionError, match="network down"):
            await _retry(always_fails, retries=3, delay=0.0, label="test")

    assert call_count == 3


# --- Tests for backfill_okx_candles ---


@pytest.fixture
def mock_candle():
    c = MagicMock()
    c.timestamp = 1700000000000
    c.open = 100.0
    c.high = 110.0
    c.low = 90.0
    c.close = 105.0
    c.volume = 1000.0
    return c


@pytest.mark.asyncio
async def test_backfill_okx_candles_uses_okx_provider(mock_candle):
    """backfill_okx_candles should fetch candles via OKXProvider for each watchlist symbol."""
    mock_okx = AsyncMock()
    mock_okx.get_ohlcv = AsyncMock(return_value=[mock_candle])
    mock_okx.close = AsyncMock()

    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session.merge = AsyncMock()
    mock_session.commit = AsyncMock()

    mock_config = {"watchlist": ["BTCUSDT", "ETHUSDT"]}

    with patch("app.worker.OKXProvider", return_value=mock_okx):
        with patch("app.worker.Database.get_session", return_value=mock_session):
            with patch(
                "app.jobs.signal_log._get_config", new_callable=AsyncMock, return_value=mock_config
            ):
                with patch("app.worker.asyncio.sleep", new_callable=AsyncMock):
                    with patch("app.schemas.activity_log.log_activity", new_callable=AsyncMock):
                        with patch(
                            "app.worker._retry", new_callable=AsyncMock, return_value=[mock_candle]
                        ) as mock_retry:
                            await backfill_okx_candles({})

    mock_okx.close.assert_awaited_once()
    assert mock_retry.call_count == len(mock_config["watchlist"]) * 4  # 4 timeframes


@pytest.mark.asyncio
async def test_backfill_okx_candles_handles_provider_error():
    """backfill_okx_candles should not propagate exceptions when OKX is unreachable."""
    mock_okx = AsyncMock()
    mock_okx.close = AsyncMock()

    mock_config = {"watchlist": ["BTCUSDT"]}

    with patch("app.worker.OKXProvider", return_value=mock_okx):
        with patch("app.worker.asyncio.sleep", new_callable=AsyncMock):
            with patch(
                "app.jobs.signal_log._get_config", new_callable=AsyncMock, return_value=mock_config
            ):
                with patch("app.schemas.activity_log.log_activity", new_callable=AsyncMock):
                    with patch(
                        "app.worker._retry",
                        new_callable=AsyncMock,
                        side_effect=Exception("OKX unreachable"),
                    ):
                        # Must not raise
                        await backfill_okx_candles({})

    mock_okx.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# execute_signals — regime gate + staleness gate
# ---------------------------------------------------------------------------


def _make_signal(symbol="BTCUSDT", direction="LONG", fired_at_offset_ms=0):
    """Create a mock SignalLog for execute_signals tests.

    fired_at_offset_ms is subtracted from now so positive values mean 'in the past'.
    Default 0 == now (fresh signal).
    """
    now_ms = int(time.time() * 1000)
    sig = MagicMock()
    sig.id = 1
    sig.symbol = symbol
    sig.direction = direction
    sig.fired_at = now_ms - fired_at_offset_ms
    return sig


def _build_patches(signals, regime_payload, trading_enabled=True):
    """Return a list of patch objects that stub all execute_signals dependencies."""
    # DB session returns the provided signals list
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = signals
    mock_session.execute = AsyncMock(return_value=mock_result)

    config = {"enabled": trading_enabled, "initial_capital": 100.0}
    signal_config = {"watchlist": [s.symbol for s in signals]}

    return [
        patch("app.worker.get_trading_config", new_callable=AsyncMock, return_value=config),
        patch("app.worker.Database.get_session", return_value=mock_session),
        patch(
            "app.jobs.signal_log._get_config", new_callable=AsyncMock, return_value=signal_config
        ),
        patch(
            "app.worker.RedisClient.get_json", new_callable=AsyncMock, return_value=regime_payload
        ),
        patch(
            "app.worker._trade_orchestrator.process_signal",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ]


@pytest.mark.asyncio
async def test_execute_signals_regime_bear_blocks_long():
    """Regime gate: BEAR regime drops LONG signals — orchestrator is never called."""
    long_signal = _make_signal(direction="LONG")
    patches = _build_patches([long_signal], regime_payload={"regime": "BEAR"})

    with patches[0], patches[1], patches[2], patches[3], patches[4] as mock_process:
        await execute_signals({})
        mock_process.assert_not_called()


@pytest.mark.asyncio
async def test_execute_signals_regime_bear_passes_short():
    """Regime gate: BEAR regime passes SHORT signals through to orchestrator."""
    short_signal = _make_signal(direction="SHORT")
    patches = _build_patches([short_signal], regime_payload={"regime": "BEAR"})

    with patches[0], patches[1], patches[2], patches[3], patches[4] as mock_process:
        await execute_signals({})
        mock_process.assert_awaited_once_with(short_signal, batch_positions=[])


@pytest.mark.asyncio
async def test_execute_signals_regime_unknown_passes_all():
    """Regime gate: UNKNOWN regime lets both LONG and SHORT through."""
    long_signal = _make_signal(symbol="BTCUSDT", direction="LONG")
    short_signal = _make_signal(symbol="ETHUSDT", direction="SHORT")
    short_signal.id = 2
    patches = _build_patches(
        [long_signal, short_signal],
        regime_payload={"regime": "UNKNOWN"},
    )

    with patches[0], patches[1], patches[2], patches[3], patches[4] as mock_process:
        await execute_signals({})
        assert mock_process.await_count == 2


@pytest.mark.asyncio
async def test_execute_signals_regime_none_passes_all():
    """Regime gate: missing Redis key (None) is treated as UNKNOWN — both pass."""
    long_signal = _make_signal(symbol="BTCUSDT", direction="LONG")
    short_signal = _make_signal(symbol="ETHUSDT", direction="SHORT")
    short_signal.id = 2
    patches = _build_patches(
        [long_signal, short_signal],
        regime_payload=None,  # Redis returns None
    )

    with patches[0], patches[1], patches[2], patches[3], patches[4] as mock_process:
        await execute_signals({})
        assert mock_process.await_count == 2


@pytest.mark.asyncio
async def test_execute_signals_staleness_drops_old_signal():
    """Staleness gate: signal older than 12 hours is filtered out."""
    thirteen_hours_ms = 13 * 60 * 60 * 1000
    old_signal = _make_signal(fired_at_offset_ms=thirteen_hours_ms)
    patches = _build_patches([old_signal], regime_payload={"regime": "UNKNOWN"})

    with patches[0], patches[1], patches[2], patches[3], patches[4] as mock_process:
        await execute_signals({})
        mock_process.assert_not_called()


@pytest.mark.asyncio
async def test_execute_signals_staleness_passes_fresh_signal():
    """Staleness gate: signal fired 1 hour ago passes through."""
    one_hour_ms = 1 * 60 * 60 * 1000
    fresh_signal = _make_signal(fired_at_offset_ms=one_hour_ms)
    patches = _build_patches([fresh_signal], regime_payload={"regime": "UNKNOWN"})

    with patches[0], patches[1], patches[2], patches[3], patches[4] as mock_process:
        await execute_signals({})
        mock_process.assert_awaited_once_with(fresh_signal, batch_positions=[])
