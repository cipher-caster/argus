"""
Tests for optimization and trade analysis routes.

Covers:
- /api/optimization/experiments, /best, /{id} — experiment CRUD
- /api/trading/analysis — trade analysis grouping
- /api/trading/analysis/recommendations — config recommendations
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_experiment(**overrides):
    defaults = dict(
        id=1,
        run_id="test-run",
        name="test_config",
        created_at=1700000000000,
        symbols="BTC,ETH,BNB",
        sl_mult=1.5,
        tp_mult=2.5,
        tp_adaptive=False,
        min_titan_confidence=55,
        block_sleeping=True,
        block_volatile=True,
        macro_guard=True,
        strict_macro=False,
        min_conviction=65,
        total_signals=50,
        wins=25,
        losses=20,
        reviews=5,
        win_rate=55.6,
        total_r=12.5,
        ev_per_trade=0.25,
        avg_rr=1.8,
        coin_results='{"BTC": {"wins": 10, "losses": 8}}',
        notes=None,
        is_production=False,
    )
    defaults.update(overrides)
    exp = MagicMock()
    for k, v in defaults.items():
        setattr(exp, k, v)
    return exp


def _make_position(
    symbol="BTCUSDT",
    direction="LONG",
    outcome="WIN",
    status="CLOSED",
    conviction=70,
    market_state="TRENDING",
    intended_entry=50000.0,
    intended_tp=55000.0,
    intended_sl=48000.0,
    filled_at=1700000000000,
    closed_at=1700010000000,
    pnl_usd=50.0,
    pnl_pct=5.0,
):
    pos = MagicMock()
    pos.symbol = symbol
    pos.direction = direction
    pos.outcome = outcome
    pos.status = status
    pos.conviction = conviction
    pos.market_state = market_state
    pos.intended_entry = intended_entry
    pos.intended_tp = intended_tp
    pos.intended_sl = intended_sl
    pos.filled_at = filled_at
    pos.closed_at = closed_at
    pos.pnl_usd = pnl_usd
    pos.pnl_pct = pnl_pct
    return pos


# ---------------------------------------------------------------------------
# Experiment endpoints
# ---------------------------------------------------------------------------


class TestExperiments:
    @pytest.mark.asyncio
    @patch("app.routes.optimization.Database")
    async def test_list_experiments_200(self, mock_db, async_client):
        exp = _make_experiment()
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [exp]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/optimization/experiments")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "test_config"

    @pytest.mark.asyncio
    @patch("app.routes.optimization.Database")
    async def test_get_experiment_404(self, mock_db, async_client):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/optimization/experiments/99999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    @patch("app.routes.optimization.Database")
    async def test_best_experiment_200(self, mock_db, async_client):
        exp = _make_experiment(total_signals=50, ev_per_trade=0.35)
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = exp
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.get("/api/optimization/best")
        assert resp.status_code == 200
        assert resp.json()["results"]["ev_per_trade"] == 0.35


# ---------------------------------------------------------------------------
# Apply Experiment
# ---------------------------------------------------------------------------


class TestApplyExperiment:
    @pytest.mark.asyncio
    @patch("app.routes.optimization.RedisClient")
    @patch("app.routes.optimization.Database")
    async def test_apply_experiment_404(self, mock_db, mock_redis, async_client):
        """Returns 404 when experiment_id does not exist."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await async_client.post("/api/optimization/apply", json={"experiment_id": 99999})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    @patch("app.routes.optimization.RedisClient")
    @patch("app.routes.optimization.Database")
    async def test_apply_experiment_db_failure_returns_500_and_rolls_back_redis(
        self, mock_db, mock_redis, async_client
    ):
        """If the DB commit fails, returns 500 and restores original Redis values."""
        exp = _make_experiment(id=1)

        # First session call (lookup) succeeds
        lookup_session = AsyncMock()
        lookup_result = MagicMock()
        lookup_result.scalar_one_or_none.return_value = exp
        lookup_session.execute = AsyncMock(return_value=lookup_result)

        # Second session call (commit) raises
        commit_session = AsyncMock()
        commit_result = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        commit_result.scalars.return_value = scalars_mock

        scalar_one_result = MagicMock()
        scalar_one_result.scalar_one_or_none.return_value = exp

        async def _execute_side_effect(stmt):
            return commit_result

        commit_session.execute = AsyncMock(side_effect=_execute_side_effect)
        commit_session.commit = AsyncMock(side_effect=Exception("DB commit failed"))
        commit_session.add = MagicMock()

        call_count = 0

        class _SessionCtx:
            def __init__(self, session):
                self._session = session

            async def __aenter__(self):
                return self._session

            async def __aexit__(self, *args):
                return False

        sessions = [_SessionCtx(lookup_session), _SessionCtx(commit_session)]

        def _get_session():
            return sessions.pop(0)

        mock_db.get_session.side_effect = _get_session

        # Redis: r.get returns original values; track set calls
        original_sl = b'{"min_titan_confidence": 55}'
        original_t = b'{"min_conviction": 65}'
        r_mock = AsyncMock()
        r_mock.get = AsyncMock(side_effect=[original_sl, original_t])
        set_calls = []

        async def _redis_set(key, value):
            set_calls.append((key, value))

        r_mock.set = AsyncMock(side_effect=_redis_set)
        mock_redis.get_instance.return_value = r_mock

        resp = await async_client.post("/api/optimization/apply", json={"experiment_id": 1})
        assert resp.status_code == 500
        assert "Failed to apply experiment" in resp.json()["detail"]

        # Redis should have been rolled back: the last two set calls should restore originals
        rollback_calls = [(k, v) for k, v in set_calls if v in (original_sl, original_t)]
        assert len(rollback_calls) == 2, (
            f"Expected 2 rollback Redis set calls, got {len(rollback_calls)}. All calls: {set_calls}"
        )


# ---------------------------------------------------------------------------
# Trade Analysis
# ---------------------------------------------------------------------------


class TestTradeAnalysis:
    @pytest.mark.asyncio
    @patch("app.routes.optimization.TradeAnalyzer")
    async def test_analysis_empty(self, mock_analyzer, async_client):
        mock_analyzer.analyze_closed_trades = AsyncMock(
            return_value={
                "total_closed": 0,
                "message": "No closed positions yet. Paper trading needs more time.",
                "by_symbol": {},
                "by_direction": {},
                "by_market_state": {},
                "by_conviction_bucket": {},
                "streak_analysis": {},
                "rejection_count": 0,
            }
        )

        resp = await async_client.get("/api/trading/analysis")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_closed"] == 0
        assert "message" in data

    @pytest.mark.asyncio
    @patch("app.routes.optimization.TradeAnalyzer")
    async def test_analysis_grouped(self, mock_analyzer, async_client):
        mock_analyzer.analyze_closed_trades = AsyncMock(
            return_value={
                "total_closed": 5,
                "by_symbol": {
                    "BTCUSDT": {
                        "count": 3,
                        "wins": 2,
                        "losses": 1,
                        "win_rate": 66.7,
                        "profit_r": 2.0,
                        "avg_hold_hours": 12.0,
                    },
                    "ETHUSDT": {
                        "count": 2,
                        "wins": 1,
                        "losses": 1,
                        "win_rate": 50.0,
                        "profit_r": 0.5,
                        "avg_hold_hours": 8.0,
                    },
                },
                "by_direction": {
                    "LONG": {
                        "count": 4,
                        "wins": 3,
                        "losses": 1,
                        "win_rate": 75.0,
                        "profit_r": 3.0,
                        "avg_hold_hours": 10.0,
                    },
                    "SHORT": {
                        "count": 1,
                        "wins": 0,
                        "losses": 1,
                        "win_rate": 0.0,
                        "profit_r": -1.0,
                        "avg_hold_hours": 6.0,
                    },
                },
                "by_market_state": {
                    "TRENDING": {
                        "count": 5,
                        "wins": 3,
                        "losses": 2,
                        "win_rate": 60.0,
                        "profit_r": 2.5,
                        "avg_hold_hours": 10.0,
                    }
                },
                "by_conviction_bucket": {
                    "75+": {
                        "count": 3,
                        "wins": 2,
                        "losses": 1,
                        "win_rate": 66.7,
                        "profit_r": 2.0,
                        "avg_hold_hours": 10.0,
                    }
                },
                "streak_analysis": {
                    "longest_win_streak": 2,
                    "longest_loss_streak": 1,
                    "current_streak": {"type": "WIN", "length": 1},
                },
                "rejection_count": 2,
            }
        )

        resp = await async_client.get("/api/trading/analysis")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_closed"] == 5
        assert "BTCUSDT" in data["by_symbol"]
        assert "LONG" in data["by_direction"]
        assert data["streak_analysis"]["longest_win_streak"] == 2

    @pytest.mark.asyncio
    @patch("app.routes.optimization.TradeAnalyzer")
    async def test_recommendations_insufficient_data(self, mock_analyzer, async_client):
        mock_analyzer.recommend_config = AsyncMock(
            return_value=[
                {
                    "param": "data",
                    "current_value": 3,
                    "suggested_value": 10,
                    "reason": "Not enough closed trades for reliable recommendations",
                    "evidence": "Only 3 closed trades. Need at least 10.",
                }
            ]
        )

        resp = await async_client.get("/api/trading/analysis/recommendations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["param"] == "data"

    @pytest.mark.asyncio
    @patch("app.routes.optimization.TradeAnalyzer")
    async def test_recommendations_poor_coin(self, mock_analyzer, async_client):
        mock_analyzer.recommend_config = AsyncMock(
            return_value=[
                {
                    "param": "watchlist",
                    "current_value": "DOGEUSDT",
                    "suggested_value": "remove DOGEUSDT",
                    "reason": "DOGEUSDT is consistently losing in live trading",
                    "evidence": "WR=20.0% over 5 trades, profit=-3.00R",
                }
            ]
        )

        resp = await async_client.get("/api/trading/analysis/recommendations")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["param"] == "watchlist"
        assert "remove" in data[0]["suggested_value"]
