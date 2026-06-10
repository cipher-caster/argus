"""
Tests for indicator and system API routes.

Covers:
- GET /api/indicators/ — list available indicators
- POST /api/indicators/calculate — calculate indicators (DB + provider fallback)
- GET /api/indicators/market/dashboard — dashboard market indicators
- GET /api/system/activity-log — activity log with filtering
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Indicator Routes
# ---------------------------------------------------------------------------


class TestIndicatorList:
    @pytest.mark.asyncio
    async def test_list_returns_200(self, async_client):
        resp = await async_client.get("/api/indicators/")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_has_definitions(self, async_client):
        resp = await async_client.get("/api/indicators/")
        data = resp.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "type" in data[0] or "name" in data[0]


class TestIndicatorCalculate:
    @pytest.mark.asyncio
    @patch("app.storage.Database")
    async def test_calculate_returns_results(self, mock_db, async_client):
        """DB has candles → indicators calculated."""
        candles = []
        for i in range(50):
            c = MagicMock()
            c.timestamp = 1700000000000 + i * 3600000
            c.open = 50000.0 + i * 10
            c.high = 50500.0 + i * 10
            c.low = 49500.0 + i * 10
            c.close = 50200.0 + i * 10
            c.volume = 1000.0
            candles.append(c)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = candles
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.post(
            "/api/indicators/calculate",
            json={
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "indicators": [{"type": "ema", "params": {"length": 20}}],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["symbol"] == "BTC/USDT"

    @pytest.mark.asyncio
    @patch("app.routes.indicators.get_provider")
    @patch("app.storage.Database")
    async def test_calculate_fallback_to_provider(self, mock_db, mock_prov, async_client):
        """Empty DB → falls back to provider."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        candles = []
        for i in range(50):
            c = MagicMock()
            c.timestamp = 1700000000000 + i * 3600000
            c.open = 50000.0 + i * 10
            c.high = 50500.0 + i * 10
            c.low = 49500.0 + i * 10
            c.close = 50200.0 + i * 10
            c.volume = 1000.0
            candles.append(c)

        provider = AsyncMock()
        provider.get_ohlcv = AsyncMock(return_value=candles)
        mock_prov.return_value = provider

        resp = await async_client.post(
            "/api/indicators/calculate",
            json={
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "indicators": [{"type": "ema", "params": {"length": 20}}],
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @patch("app.routes.indicators.get_provider")
    @patch("app.storage.Database")
    async def test_calculate_invalid_returns_400(self, mock_db, mock_prov, async_client):
        """Empty DB + empty provider data → 400."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        provider = AsyncMock()
        provider.get_ohlcv = AsyncMock(return_value=[])
        mock_prov.return_value = provider

        resp = await async_client.post(
            "/api/indicators/calculate",
            json={
                "symbol": "INVALID/PAIR",
                "timeframe": "1h",
                "indicators": [{"type": "ema", "params": {"length": 20}}],
            },
        )
        assert resp.status_code == 400


class TestMarketDashboard:
    @pytest.mark.asyncio
    @patch("app.routes.indicators.RedisClient")
    @patch("app.storage.Database")
    async def test_dashboard_returns_all_keys(self, mock_db, mock_redis, async_client):
        """Dashboard returns expected top-level keys."""
        candles = []
        for i in range(30):
            c = MagicMock()
            c.timestamp = 1700000000000 + i * 86400000
            c.open = 50000.0 + i * 100
            c.high = 50500.0 + i * 100
            c.low = 49500.0 + i * 100
            c.close = 50200.0 + i * 100
            c.volume = 5000.0
            candles.append(c)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = candles
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_redis.get_json = AsyncMock(return_value=None)
        mock_redis.set_json = AsyncMock(return_value=True)

        resp = await async_client.get("/api/indicators/market/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "btc_volatility" in data
        assert "market_adx" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    @patch("app.routes.indicators.RedisClient")
    @patch("app.storage.Database")
    async def test_dashboard_handles_empty(self, mock_db, mock_redis, async_client):
        """No data available → returns null values, not error."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_redis.get_json = AsyncMock(return_value=None)
        mock_redis.set_json = AsyncMock(return_value=True)

        resp = await async_client.get("/api/indicators/market/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["btc_volatility"] is None

    @pytest.mark.asyncio
    @patch("app.routes.indicators.RedisClient")
    @patch("app.storage.Database")
    async def test_dashboard_cache_hit_skips_db(self, mock_db, mock_redis, async_client):
        """Cache hit returns cached result immediately without querying DB."""
        cached_payload = {
            "btc_volatility": {"value": 2.5},
            "market_adx": {"value": 30.0},
            "total_market_cap": None,
            "btc_dominance": None,
            "updated_at": "2026-01-01T00:00:00",
        }

        mock_redis.get_json = AsyncMock(return_value=cached_payload)
        mock_redis.set_json = AsyncMock()

        resp = await async_client.get("/api/indicators/market/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["btc_volatility"] == {"value": 2.5}
        # DB must not have been touched on a cache hit
        mock_db.get_session.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.routes.indicators.RedisClient")
    @patch("app.storage.Database")
    async def test_dashboard_error_returns_generic_message(self, mock_db, mock_redis, async_client):
        """Unexpected exception returns 500 with generic message, not raw error internals."""
        mock_redis.get_json = AsyncMock(return_value=None)
        mock_redis.set_json = AsyncMock()

        # Force an unexpected error during DB access
        mock_db.get_session.return_value.__aenter__ = AsyncMock(
            side_effect=RuntimeError("internal db secret details")
        )
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/indicators/market/dashboard")
        assert resp.status_code == 500
        detail = resp.json()["detail"]
        assert "internal db secret details" not in detail
        assert detail == "Failed to calculate dashboard indicators"


# ---------------------------------------------------------------------------
# System Routes
# ---------------------------------------------------------------------------


class TestActivityLog:
    @pytest.mark.asyncio
    @patch("app.routes.system.Database")
    async def test_activity_log_200(self, mock_db, async_client):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/system/activity-log")
        assert resp.status_code == 200
        assert "data" in resp.json()

    @pytest.mark.asyncio
    @patch("app.routes.system.Database")
    async def test_respects_limit(self, mock_db, async_client):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/system/activity-log?limit=10")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @patch("app.routes.system.Database")
    async def test_filters_by_event_type(self, mock_db, async_client):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/system/activity-log?event_type=STARTUP")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Health Endpoint
# ---------------------------------------------------------------------------


class TestHealthCheck:
    @pytest.mark.asyncio
    @patch("app.storage.RedisClient")
    @patch("app.storage.Database")
    async def test_health_returns_200_when_redis_ok(self, mock_db, mock_redis, async_client):
        """Health endpoint returns 200 with status 'healthy' when Redis is available."""
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock(return_value=True)
        mock_redis.get_instance.return_value = mock_redis_instance
        mock_db._engine = object()  # engine is not None → database ok

        resp = await async_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "redis" in data
        assert "database" in data

    @pytest.mark.asyncio
    @patch("app.storage.RedisClient")
    @patch("app.storage.Database")
    async def test_health_returns_503_when_redis_down(self, mock_db, mock_redis, async_client):
        """Health endpoint returns 503 with status 'degraded' when Redis is unavailable."""
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock(side_effect=Exception("Connection refused"))
        mock_redis.get_instance.return_value = mock_redis_instance
        mock_db._engine = object()  # engine is not None → database ok

        resp = await async_client.get("/health")
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["redis"] == "unavailable"
