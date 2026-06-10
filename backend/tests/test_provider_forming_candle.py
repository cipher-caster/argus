"""
Tests that BinanceProvider and OKXProvider drop the still-forming
(open) candle from the tail of every OHLCV response.

Change 1 of the P0 Trading Correctness plan:
  - Provider requests limit+1 rows from the exchange.
  - The last row (the forming candle) is stripped before returning.
  - Callers that ask for N candles receive N closed candles.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.providers.binance_provider import BinanceProvider
from app.providers.okx_provider import OKXProvider

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_raw_ohlcv(n: int) -> list:
    """Return n synthetic OHLCV rows as the exchange would: [[ts, o, h, l, c, v], ...]."""
    base_ts = 1_700_000_000_000  # arbitrary ms timestamp
    return [
        [base_ts + i * 3_600_000, 100.0 + i, 105.0 + i, 95.0 + i, 102.0 + i, 1000.0]
        for i in range(n)
    ]


def _patch_binance_exchange(raw_rows: list):
    """Return a MagicMock that stands in for the ccxt.binance exchange object."""
    mock_exchange = MagicMock()
    mock_exchange.markets = {"BTC/USDT": {}}  # ensure _ensure_loaded is a no-op
    mock_exchange.load_markets = AsyncMock()
    mock_exchange.fetch_ohlcv = AsyncMock(return_value=raw_rows)
    return mock_exchange


def _patch_okx_exchange(raw_rows: list):
    """Return a MagicMock that stands in for the ccxt.okx exchange object."""
    mock_exchange = MagicMock()
    mock_exchange.markets = {"BTC/USDT": {}}
    mock_exchange.load_markets = AsyncMock()
    mock_exchange.fetch_ohlcv = AsyncMock(return_value=raw_rows)
    return mock_exchange


# ---------------------------------------------------------------------------
# BinanceProvider tests
# ---------------------------------------------------------------------------


class TestBinanceProviderFormingCandle:
    @pytest.mark.asyncio
    async def test_drops_forming_candle_returns_limit_rows(self):
        """When exchange returns limit+1 rows, provider drops last and returns limit rows."""
        limit = 10
        raw = _make_raw_ohlcv(limit + 1)  # exchange returns 11 rows

        provider = BinanceProvider.__new__(BinanceProvider)
        provider._symbols_cache = None
        provider._exchange = _patch_binance_exchange(raw)

        candles = await provider.get_ohlcv("BTC/USDT", timeframe="4h", limit=limit)

        assert len(candles) == limit, f"Expected {limit} closed candles, got {len(candles)}"

    @pytest.mark.asyncio
    async def test_last_candle_is_not_forming(self):
        """The last returned candle must not be the originally-last (forming) row."""
        limit = 5
        raw = _make_raw_ohlcv(limit + 1)
        forming_ts = raw[-1][0]  # timestamp of the forming candle

        provider = BinanceProvider.__new__(BinanceProvider)
        provider._symbols_cache = None
        provider._exchange = _patch_binance_exchange(raw)

        candles = await provider.get_ohlcv("BTC/USDT", timeframe="1h", limit=limit)

        returned_ts = [c.timestamp for c in candles]
        assert forming_ts not in returned_ts, (
            "Forming candle timestamp must not appear in returned candles"
        )

    @pytest.mark.asyncio
    async def test_requests_limit_plus_one_from_exchange(self):
        """Provider must request limit+1 rows from CCXT to guarantee limit closed rows."""
        limit = 20
        raw = _make_raw_ohlcv(limit + 1)

        provider = BinanceProvider.__new__(BinanceProvider)
        provider._symbols_cache = None
        provider._exchange = _patch_binance_exchange(raw)

        await provider.get_ohlcv("BTC/USDT", timeframe="4h", limit=limit)

        call_kwargs = provider._exchange.fetch_ohlcv.call_args
        actual_limit_arg = call_kwargs.kwargs.get("limit") or call_kwargs.args[2]
        assert actual_limit_arg == limit + 1, (
            f"Expected CCXT to be called with limit={limit + 1}, got {actual_limit_arg}"
        )

    @pytest.mark.asyncio
    async def test_empty_exchange_response_returns_empty(self):
        """An empty exchange response is handled gracefully (no IndexError)."""
        provider = BinanceProvider.__new__(BinanceProvider)
        provider._symbols_cache = None
        provider._exchange = _patch_binance_exchange([])

        candles = await provider.get_ohlcv("BTC/USDT", timeframe="4h", limit=10)

        assert candles == []

    @pytest.mark.asyncio
    async def test_single_row_exchange_response_returns_empty(self):
        """If exchange returns only 1 row (the forming candle), result is empty — no closed candles."""
        provider = BinanceProvider.__new__(BinanceProvider)
        provider._symbols_cache = None
        provider._exchange = _patch_binance_exchange(_make_raw_ohlcv(1))

        candles = await provider.get_ohlcv("BTC/USDT", timeframe="4h", limit=1)

        assert candles == [], (
            "A single row from the exchange is the forming candle and must be dropped"
        )


# ---------------------------------------------------------------------------
# OKXProvider tests
# ---------------------------------------------------------------------------


class TestOKXProviderFormingCandle:
    @pytest.mark.asyncio
    async def test_drops_forming_candle_returns_limit_rows(self):
        """When exchange returns limit+1 rows, provider drops last and returns limit rows."""
        limit = 10
        raw = _make_raw_ohlcv(limit + 1)

        provider = OKXProvider.__new__(OKXProvider)
        provider._symbols_cache = None
        provider._exchange = _patch_okx_exchange(raw)

        candles = await provider.get_ohlcv("BTC/USDT", timeframe="4h", limit=limit)

        assert len(candles) == limit, f"Expected {limit} closed candles, got {len(candles)}"

    @pytest.mark.asyncio
    async def test_last_candle_is_not_forming(self):
        """The last returned candle must not be the originally-last (forming) row."""
        limit = 5
        raw = _make_raw_ohlcv(limit + 1)
        forming_ts = raw[-1][0]

        provider = OKXProvider.__new__(OKXProvider)
        provider._symbols_cache = None
        provider._exchange = _patch_okx_exchange(raw)

        candles = await provider.get_ohlcv("BTC/USDT", timeframe="1h", limit=limit)

        returned_ts = [c.timestamp for c in candles]
        assert forming_ts not in returned_ts

    @pytest.mark.asyncio
    async def test_requests_limit_plus_one_from_exchange(self):
        """Provider must request limit+1 rows from CCXT."""
        limit = 20
        raw = _make_raw_ohlcv(limit + 1)

        provider = OKXProvider.__new__(OKXProvider)
        provider._symbols_cache = None
        provider._exchange = _patch_okx_exchange(raw)

        await provider.get_ohlcv("BTC/USDT", timeframe="4h", limit=limit)

        call_kwargs = provider._exchange.fetch_ohlcv.call_args
        actual_limit_arg = call_kwargs.kwargs.get("limit") or call_kwargs.args[2]
        assert actual_limit_arg == limit + 1

    @pytest.mark.asyncio
    async def test_empty_exchange_response_returns_empty(self):
        """An empty exchange response is handled gracefully."""
        provider = OKXProvider.__new__(OKXProvider)
        provider._symbols_cache = None
        provider._exchange = _patch_okx_exchange([])

        candles = await provider.get_ohlcv("BTC/USDT", timeframe="4h", limit=10)

        assert candles == []
