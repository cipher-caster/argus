"""
Integration tests for analytics API endpoints.
Requires the full app stack (Redis + external calls are mocked).
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# Shared helpers from conftest.py
from conftest import (
    mock_cache_miss, mock_cache_hit,
    MOCK_SCREENER_DATA, MOCK_SYMBOLS, VALID_MARKET_STATES,
)




# ---------------------------------------------------------------------------
# /api/analytics/screener
# ---------------------------------------------------------------------------

class TestScreenerEndpoint:
    @pytest.mark.asyncio
    async def test_screener_returns_200(self, async_client):
        cached = {"data": MOCK_SCREENER_DATA, "last_updated": 1700000000000}
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/screener?limit=4&timeframe=1h")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_screener_response_shape(self, async_client):
        cached = {"data": MOCK_SCREENER_DATA, "last_updated": 1700000000000}
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/screener?limit=4&timeframe=1h")
        body = response.json()
        assert "data" in body
        assert "last_updated" in body
        assert isinstance(body["data"], list)

    @pytest.mark.asyncio
    async def test_screener_each_item_has_symbol_and_score(self, async_client):
        cached = {"data": MOCK_SCREENER_DATA, "last_updated": 1700000000000}
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/screener?limit=4&timeframe=1h")
        for item in response.json()["data"]:
            assert "symbol" in item
            assert "score" in item
            assert -4 <= item["score"] <= 4


# ---------------------------------------------------------------------------
# /api/analytics/signal-summary
# ---------------------------------------------------------------------------

class TestSignalSummaryEndpoint:
    @pytest.mark.asyncio
    async def test_signal_summary_returns_200(self, async_client):
        cached = {
            "bullish_pct": 50.0,
            "bearish_pct": 25.0,
            "top_signals": ["BTCUSDT 3/4"],
            "market_state": "STRONG BULL",
            "last_updated": 1700000000000,
        }
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/signal-summary")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_signal_summary_market_state_is_valid(self, async_client):
        cached = {
            "bullish_pct": 50.0,
            "bearish_pct": 25.0,
            "top_signals": [],
            "market_state": "STRONG BULL",
            "last_updated": 1700000000000,
        }
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/signal-summary")
        assert response.json()["market_state"] in VALID_MARKET_STATES

    @pytest.mark.asyncio
    async def test_signal_summary_pct_fields_are_numeric(self, async_client):
        cached = {
            "bullish_pct": 52.0,
            "bearish_pct": 18.0,
            "top_signals": [],
            "market_state": "NEUTRAL",
            "last_updated": 1700000000000,
        }
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/signal-summary")
        body = response.json()
        assert isinstance(body["bullish_pct"], (int, float))
        assert isinstance(body["bearish_pct"], (int, float))

    @pytest.mark.asyncio
    async def test_market_state_derived_correctly_strong_bull(self, async_client):
        """When >50% bullish and 2x more bulls than bears → STRONG BULL."""
        with patch("app.routes.analytics.RedisClient", mock_cache_miss()), \
             patch("app.routes.analytics.MarketDataService.get_top_symbols", AsyncMock(return_value=MOCK_SYMBOLS)), \
             patch("app.routes.analytics.fetch_all_candles", AsyncMock(return_value={})), \
             patch("app.routes.analytics.run_oracle_screener", return_value=[
                 {"symbol": "A", "score": 2},
                 {"symbol": "B", "score": 2},
                 {"symbol": "C", "score": 2},
                 {"symbol": "D", "score": -1},
             ]):
            response = await async_client.get("/api/analytics/signal-summary")
        assert response.status_code == 200
        assert response.json()["market_state"] == "STRONG BULL"

    @pytest.mark.asyncio
    async def test_market_state_derived_correctly_sleeping(self, async_client):
        """When >50% neutral (score=0) → SLEEPING."""
        with patch("app.routes.analytics.RedisClient", mock_cache_miss()), \
             patch("app.routes.analytics.MarketDataService.get_top_symbols", AsyncMock(return_value=MOCK_SYMBOLS)), \
             patch("app.routes.analytics.fetch_all_candles", AsyncMock(return_value={})), \
             patch("app.routes.analytics.run_oracle_screener", return_value=[
                 {"symbol": "A", "score": 0},
                 {"symbol": "B", "score": 0},
                 {"symbol": "C", "score": 0},
                 {"symbol": "D", "score": 1},
             ]):
            response = await async_client.get("/api/analytics/signal-summary")
        assert response.json()["market_state"] == "SLEEPING"


# ---------------------------------------------------------------------------
# /api/analytics/best-setups
# ---------------------------------------------------------------------------

class TestBestSetupsEndpoint:
    @pytest.mark.asyncio
    async def test_best_setups_returns_200(self, async_client):
        cached = {"data": [], "last_updated": 1700000000000}
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/best-setups")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_best_setups_item_shape(self, async_client):
        item = {
            "symbol": "BTCUSDT", "direction": "LONG", "conviction": 80,
            "entry": 50000.0, "tp": 52000.0, "sl": 49000.0,
            "reason": "Oracle BULLISH +3/4 | Uptrend", "oracle_score": 3, "titan_signal": "BUY",
        }
        cached = {"data": [item], "last_updated": 1700000000000}
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/best-setups")
        body = response.json()
        assert len(body["data"]) == 1
        for field in ("symbol", "direction", "conviction", "entry", "tp", "sl", "reason"):
            assert field in body["data"][0]

    @pytest.mark.asyncio
    async def test_best_setups_direction_is_long_or_short(self, async_client):
        items = [
            {"symbol": "BTCUSDT", "direction": "LONG", "conviction": 80,
             "entry": 50000.0, "tp": 52000.0, "sl": 49000.0,
             "reason": "r", "oracle_score": 3, "titan_signal": "BUY"},
            {"symbol": "ETHUSDT", "direction": "SHORT", "conviction": 70,
             "entry": 2000.0, "tp": 1900.0, "sl": 2100.0,
             "reason": "r", "oracle_score": -3, "titan_signal": "SELL"},
        ]
        cached = {"data": items, "last_updated": 1700000000000}
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/best-setups")
        for item in response.json()["data"]:
            assert item["direction"] in ("LONG", "SHORT")

    @pytest.mark.asyncio
    async def test_best_setups_conviction_in_range(self, async_client):
        item = {
            "symbol": "BTCUSDT", "direction": "LONG", "conviction": 85,
            "entry": 50000.0, "tp": 52000.0, "sl": 49000.0,
            "reason": "r", "oracle_score": 3, "titan_signal": "BUY",
        }
        cached = {"data": [item], "last_updated": 1700000000000}
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/best-setups")
        for item in response.json()["data"]:
            assert 0 <= item["conviction"] <= 100

    @pytest.mark.asyncio
    async def test_best_setups_filters_low_oracle_score(self, async_client):
        """Oracle abs(score) < 2 should be excluded from best setups."""
        import pandas as pd
        import numpy as np

        n = 250
        prices = np.linspace(50, 200, n)
        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=n, freq="4h"),
            "open": prices, "high": prices * 1.005, "low": prices * 0.995,
            "close": prices, "volume": np.ones(n) * 1000,
        })

        low_score_oracle = [{"symbol": "BTCUSDT", "score": 1, "bias": "BULLISH", "state": "TRENDING"}]

        with patch("app.routes.analytics.RedisClient", mock_cache_miss()), \
             patch("app.routes.analytics.MarketDataService.get_top_symbols", AsyncMock(return_value=["BTCUSDT"])), \
             patch("app.routes.analytics.fetch_all_candles", AsyncMock(return_value={"BTCUSDT": df})), \
             patch("app.routes.analytics.run_oracle_screener", return_value=low_score_oracle):
            response = await async_client.get("/api/analytics/best-setups?timeframe=4h&limit=1")
        assert response.status_code == 200
        assert response.json()["data"] == []


# ---------------------------------------------------------------------------
# /api/analytics/titan-radar
# ---------------------------------------------------------------------------

class TestTitanRadarEndpoint:
    @pytest.mark.asyncio
    async def test_titan_radar_returns_200(self, async_client):
        cached = {"data": [], "last_updated": 1700000000000}
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/titan-radar")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_titan_radar_item_shape(self, async_client):
        item = {
            "symbol": "BTCUSDT", "price": 50000.0, "signal": "BUY",
            "confidence": 80, "trend": "BULLISH", "momentum": "BULLISH",
            "volatility": "NORMAL", "entry": 50000.0, "tp": 51500.0,
            "sl": 49000.0, "advice": "Aggressive (10% Risk)", "reasons": ["Uptrend"],
        }
        cached = {"data": [item], "last_updated": 1700000000000}
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/titan-radar")
        body = response.json()
        assert len(body["data"]) == 1
        for field in ("symbol", "signal", "confidence", "trend"):
            assert field in body["data"][0]

    @pytest.mark.asyncio
    async def test_titan_radar_signal_is_valid(self, async_client):
        valid_signals = {"BUY", "SELL", "BUY_LIMIT", "SELL_LIMIT", "WAIT_OB", "WAIT_OS", "NEUTRAL"}
        item = {
            "symbol": "BTCUSDT", "price": 50000.0, "signal": "BUY",
            "confidence": 80, "trend": "BULLISH", "momentum": "BULLISH",
            "volatility": "NORMAL", "entry": 50000.0, "tp": 51500.0,
            "sl": 49000.0, "advice": "Aggressive (10% Risk)", "reasons": [],
        }
        cached = {"data": [item], "last_updated": 1700000000000}
        with patch("app.routes.analytics.RedisClient", mock_cache_hit(cached)):
            response = await async_client.get("/api/analytics/titan-radar")
        for item in response.json()["data"]:
            assert item["signal"] in valid_signals
