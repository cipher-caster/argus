"""
Tests for trading API routes (/api/trading/*).

Covers:
- Portfolio: shape, mode, equity calc
- Positions: list, filter by status/symbol, 404
- History: closed only, limit
- Config: get, put merge, put ignores null
- Close: success, 404, close-all
- Pause + Stats
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_config(**overrides):
    base = {
        "enabled": True,
        "initial_capital": 1000.0,
        "max_position_size_pct": 10.0,
        "max_concurrent_positions": 3,
        "max_correlated_positions": 2,
        "max_drawdown_pct": 15.0,
        "min_conviction": 60,
        "order_expiry_hours": 8,
    }
    base.update(overrides)
    return base


def _make_position_obj(**overrides):
    """Return a MagicMock that looks like a Position ORM object."""
    defaults = dict(
        id=1, signal_log_id=10, symbol="BTCUSDT", direction="LONG",
        status="OPEN", intended_entry=50000.0, actual_entry=50100.0,
        intended_tp=55000.0, intended_sl=48000.0, actual_exit=None,
        quantity=0.01, quote_amount=501.0, risk_amount=21.0,
        pnl_usd=None, pnl_pct=None, outcome=None,
        conviction=75, market_state="TRENDING", fired_reason="test",
        created_at=1700000000000, filled_at=1700000100000, closed_at=None,
    )
    defaults.update(overrides)
    pos = MagicMock()
    for k, v in defaults.items():
        setattr(pos, k, v)
    return pos


# ---------------------------------------------------------------------------
# TestPortfolio
# ---------------------------------------------------------------------------

class TestPortfolio:

    @pytest.mark.asyncio
    @patch("app.routes.trading.RedisClient")
    @patch("app.routes.trading._get_current_prices", new_callable=AsyncMock, return_value={"BTCUSDT": 50000.0})
    @patch("app.routes.trading._get_portfolio")
    @patch("app.routes.trading.get_trading_config", new_callable=AsyncMock)
    async def test_portfolio_returns_200(self, mock_cfg, mock_port, mock_prices, mock_redis, async_client):
        mock_cfg.return_value = _mock_config()
        portfolio = AsyncMock()
        portfolio.get_balance = AsyncMock(return_value=1000.0)
        portfolio.get_unrealized_pnl = AsyncMock(return_value=50.0)
        portfolio.get_exposure = AsyncMock(return_value={"total_usdt": 200, "pct_of_balance": 20, "positions": 1})
        mock_port.return_value = portfolio
        mock_redis.set_json = AsyncMock()

        resp = await async_client.get("/api/trading/portfolio")
        assert resp.status_code == 200
        data = resp.json()
        assert "balance" in data
        assert "unrealized_pnl" in data
        assert "total_equity" in data
        assert "exposure" in data
        assert "mode" in data

    @pytest.mark.asyncio
    @patch("app.routes.trading.RedisClient")
    @patch("app.routes.trading._get_current_prices", new_callable=AsyncMock, return_value={})
    @patch("app.routes.trading._get_portfolio")
    @patch("app.routes.trading.get_trading_config", new_callable=AsyncMock)
    async def test_portfolio_mode_is_paper(self, mock_cfg, mock_port, mock_prices, mock_redis, async_client):
        mock_cfg.return_value = _mock_config()
        portfolio = AsyncMock()
        portfolio.get_balance = AsyncMock(return_value=1000.0)
        portfolio.get_unrealized_pnl = AsyncMock(return_value=0.0)
        portfolio.get_exposure = AsyncMock(return_value={"total_usdt": 0, "pct_of_balance": 0, "positions": 0})
        mock_port.return_value = portfolio
        mock_redis.set_json = AsyncMock()

        resp = await async_client.get("/api/trading/portfolio")
        assert resp.json()["mode"] == "paper"

    @pytest.mark.asyncio
    @patch("app.routes.trading.RedisClient")
    @patch("app.routes.trading._get_current_prices", new_callable=AsyncMock, return_value={})
    @patch("app.routes.trading._get_portfolio")
    @patch("app.routes.trading.get_trading_config", new_callable=AsyncMock)
    async def test_portfolio_calculates_equity(self, mock_cfg, mock_port, mock_prices, mock_redis, async_client):
        mock_cfg.return_value = _mock_config()
        portfolio = AsyncMock()
        portfolio.get_balance = AsyncMock(return_value=1000.0)
        portfolio.get_unrealized_pnl = AsyncMock(return_value=50.0)
        portfolio.get_exposure = AsyncMock(return_value={"total_usdt": 0, "pct_of_balance": 0, "positions": 0})
        mock_port.return_value = portfolio
        mock_redis.set_json = AsyncMock()

        resp = await async_client.get("/api/trading/portfolio")
        assert resp.json()["total_equity"] == 1050.0


# ---------------------------------------------------------------------------
# TestPositions
# ---------------------------------------------------------------------------

class TestPositions:

    @pytest.mark.asyncio
    @patch("app.routes.trading._get_current_prices", new_callable=AsyncMock, return_value={})
    @patch("app.routes.trading.Database")
    async def test_positions_returns_list(self, mock_db, mock_prices, async_client):
        pos = _make_position_obj(status="CLOSED")
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/trading/positions")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] == 1

    @pytest.mark.asyncio
    @patch("app.routes.trading._get_current_prices", new_callable=AsyncMock, return_value={})
    @patch("app.routes.trading.Database")
    async def test_positions_filter_by_status(self, mock_db, mock_prices, async_client):
        pos = _make_position_obj(status="OPEN")
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/trading/positions?status=OPEN")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 0

    @pytest.mark.asyncio
    @patch("app.routes.trading._get_current_prices", new_callable=AsyncMock, return_value={})
    @patch("app.routes.trading.Database")
    async def test_positions_filter_by_symbol(self, mock_db, mock_prices, async_client):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/trading/positions?symbol=BTCUSDT")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @patch("app.routes.trading.Database")
    async def test_position_by_id_not_found(self, mock_db, async_client):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/trading/positions/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TestHistory
# ---------------------------------------------------------------------------

class TestHistory:

    @pytest.mark.asyncio
    @patch("app.routes.trading.Database")
    async def test_history_returns_closed(self, mock_db, async_client):
        pos = _make_position_obj(status="CLOSED", pnl_usd=25.0, outcome="WIN", closed_at=1700001000000)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/trading/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "limit" in data
        assert "offset" in data

    @pytest.mark.asyncio
    @patch("app.routes.trading.Database")
    async def test_history_respects_limit(self, mock_db, async_client):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/trading/history?limit=5")
        assert resp.status_code == 200
        assert resp.json()["limit"] == 5


# ---------------------------------------------------------------------------
# TestConfig
# ---------------------------------------------------------------------------

class TestConfig:

    @pytest.mark.asyncio
    @patch("app.routes.trading.get_trading_config", new_callable=AsyncMock)
    async def test_get_config_200(self, mock_cfg, async_client):
        mock_cfg.return_value = _mock_config()
        resp = await async_client.get("/api/trading/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "enabled" in data
        assert "initial_capital" in data

    @pytest.mark.asyncio
    @patch("app.routes.trading.save_trading_config", new_callable=AsyncMock)
    @patch("app.routes.trading.get_trading_config", new_callable=AsyncMock)
    async def test_put_config_updates(self, mock_get, mock_save, async_client):
        mock_get.return_value = _mock_config()
        resp = await async_client.put(
            "/api/trading/config",
            json={"enabled": False, "min_conviction": 70}
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False
        assert resp.json()["min_conviction"] == 70
        mock_save.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.routes.trading.save_trading_config", new_callable=AsyncMock)
    @patch("app.routes.trading.get_trading_config", new_callable=AsyncMock)
    async def test_put_config_ignores_null(self, mock_get, mock_save, async_client):
        original = _mock_config(enabled=True)
        mock_get.return_value = original
        resp = await async_client.put(
            "/api/trading/config",
            json={"enabled": None}
        )
        assert resp.status_code == 200
        # enabled should remain True since None is excluded
        assert resp.json()["enabled"] is True

    @pytest.mark.asyncio
    async def test_put_config_initial_capital_zero_returns_422(self, async_client):
        """initial_capital=0 must be rejected (gt=0 constraint)."""
        resp = await async_client.put(
            "/api/trading/config",
            json={"initial_capital": 0}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_put_config_initial_capital_negative_returns_422(self, async_client):
        """Negative initial_capital must be rejected (gt=0 constraint)."""
        resp = await async_client.put(
            "/api/trading/config",
            json={"initial_capital": -500}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_put_config_max_drawdown_over_100_returns_422(self, async_client):
        """max_drawdown_pct > 100 must be rejected (le=100 constraint)."""
        resp = await async_client.put(
            "/api/trading/config",
            json={"max_drawdown_pct": 200}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_put_config_max_drawdown_zero_returns_422(self, async_client):
        """max_drawdown_pct=0 must be rejected (gt=0 constraint)."""
        resp = await async_client.put(
            "/api/trading/config",
            json={"max_drawdown_pct": 0}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_put_config_min_conviction_over_100_returns_422(self, async_client):
        """min_conviction > 100 must be rejected (le=100 constraint)."""
        resp = await async_client.put(
            "/api/trading/config",
            json={"min_conviction": 101}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_put_config_max_concurrent_positions_zero_returns_422(self, async_client):
        """max_concurrent_positions=0 must be rejected (ge=1 constraint)."""
        resp = await async_client.put(
            "/api/trading/config",
            json={"max_concurrent_positions": 0}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_put_config_order_expiry_hours_over_168_returns_422(self, async_client):
        """order_expiry_hours > 168 (1 week) must be rejected."""
        resp = await async_client.put(
            "/api/trading/config",
            json={"order_expiry_hours": 200}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_put_config_max_leverage_over_10_returns_422(self, async_client):
        """max_leverage > 10 must be rejected (le=10.0 constraint)."""
        resp = await async_client.put(
            "/api/trading/config",
            json={"max_leverage": 15.0}
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# TestClose
# ---------------------------------------------------------------------------

class TestClose:

    @pytest.mark.asyncio
    @patch("app.routes.trading._orchestrator")
    async def test_close_position_success(self, mock_orch, async_client):
        pos = _make_position_obj(status="CLOSED", actual_exit=51000.0, pnl_usd=9.0)
        mock_orch.manual_close = AsyncMock(return_value=pos)

        resp = await async_client.post("/api/trading/close/1")
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    @pytest.mark.asyncio
    @patch("app.routes.trading._orchestrator")
    async def test_close_position_not_found(self, mock_orch, async_client):
        mock_orch.manual_close = AsyncMock(return_value=None)

        resp = await async_client.post("/api/trading/close/99999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    @patch("app.routes.trading._orchestrator")
    @patch("app.routes.trading.Database")
    async def test_close_all_returns_count(self, mock_db, mock_orch, async_client):
        pos1 = _make_position_obj(id=1, status="OPEN")
        pos2 = _make_position_obj(id=2, status="PENDING")
        pos1_closed = _make_position_obj(id=1, status="CLOSED")
        pos2_closed = _make_position_obj(id=2, status="CLOSED")

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [pos1, pos2]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_orch.manual_close = AsyncMock(side_effect=[pos1_closed, pos2_closed])

        resp = await async_client.post("/api/trading/close-all")
        assert resp.status_code == 200
        data = resp.json()
        assert data["closed"] == 2
        assert len(data["position_ids"]) == 2


# ---------------------------------------------------------------------------
# TestPauseAndStats
# ---------------------------------------------------------------------------

class TestPauseAndStats:

    @pytest.mark.asyncio
    @patch("app.routes.trading.save_trading_config", new_callable=AsyncMock)
    @patch("app.routes.trading.get_trading_config", new_callable=AsyncMock)
    async def test_pause_disables_trading(self, mock_get, mock_save, async_client):
        mock_get.return_value = _mock_config(enabled=True)
        resp = await async_client.post("/api/trading/pause")
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False
        mock_save.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.routes.trading._get_portfolio")
    @patch("app.routes.trading.get_trading_config", new_callable=AsyncMock)
    async def test_stats_returns_balance(self, mock_cfg, mock_port, async_client):
        mock_cfg.return_value = _mock_config()
        portfolio = AsyncMock()
        portfolio.get_stats = AsyncMock(return_value={
            "total_trades": 5, "wins": 3, "losses": 2,
            "win_rate": 60.0, "avg_win_pct": 3.5, "avg_loss_pct": -2.0,
            "profit_factor": 1.75, "total_pnl_usd": 15.0, "max_drawdown_pct": 5.0,
        })
        portfolio.get_equity_curve = AsyncMock(return_value=[])
        portfolio.get_balance = AsyncMock(return_value=1015.0)
        mock_port.return_value = portfolio

        resp = await async_client.get("/api/trading/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "balance" in data
        assert data["balance"] == 1015.0

    @pytest.mark.asyncio
    @patch("app.routes.trading._get_portfolio")
    @patch("app.routes.trading.get_trading_config", new_callable=AsyncMock)
    async def test_stats_includes_equity_curve(self, mock_cfg, mock_port, async_client):
        mock_cfg.return_value = _mock_config()
        portfolio = AsyncMock()
        portfolio.get_stats = AsyncMock(return_value={
            "total_trades": 1, "wins": 1, "losses": 0,
            "win_rate": 100.0, "avg_win_pct": 5.0, "avg_loss_pct": None,
            "profit_factor": None, "total_pnl_usd": 50.0, "max_drawdown_pct": 0.0,
        })
        portfolio.get_equity_curve = AsyncMock(return_value=[
            {"timestamp": 1700001000000, "balance": 1050.0, "symbol": "BTCUSDT",
             "outcome": "WIN", "pnl_usd": 50.0}
        ])
        portfolio.get_balance = AsyncMock(return_value=1050.0)
        mock_port.return_value = portfolio

        resp = await async_client.get("/api/trading/stats")
        data = resp.json()
        assert "equity_curve" in data
        assert len(data["equity_curve"]) == 1
