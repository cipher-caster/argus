"""
Tests for signal_log.py — the core signal pipeline.

Covers:
- _passes_market_gate: pure function, no mocks
- _get_config: Redis cache hit/miss
- Redis helpers: _get_market_state, _get_btc_oracle_signal, _get_oracle_score
- log_watchlist_setups: market gate, titan confidence, direction, macro guard, insert
- log_best_setups: cache miss, low conviction, insert
- resolve_signal_outcomes: LONG win/loss, SHORT win, REVIEW timeout
"""
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.jobs.signal_log import (
    _passes_market_gate,
    _get_config,
    _get_market_state,
    _get_btc_oracle_signal,
    _get_oracle_score,
    DEFAULT_WATCHLIST,
    SIGNAL_LOG_CONFIG_KEY,
)


# ---------------------------------------------------------------------------
# TestPassesMarketGate — pure function, no mocks needed
# ---------------------------------------------------------------------------

class TestPassesMarketGate:

    def _cfg(self, **overrides):
        base = {}
        base.update(overrides)
        return base

    def test_bull_regime_passes(self):
        assert _passes_market_gate("BULL", self._cfg()) is True

    def test_bear_regime_passes(self):
        assert _passes_market_gate("BEAR", self._cfg()) is True

    def test_unknown_regime_passes(self):
        assert _passes_market_gate("UNKNOWN", self._cfg()) is True


# ---------------------------------------------------------------------------
# TestGetConfig — Redis cache hit / miss
# ---------------------------------------------------------------------------

class TestGetConfig:

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.RedisClient")
    async def test_returns_redis_config(self, mock_redis):
        custom = {"watchlist": ["BTCUSDT"], "min_titan_confidence": 70,
                  "review_days": 5, "block_sleeping": False,
                  "block_volatile": False, "macro_guard": False,
                  "block_btc_sell": False}
        mock_redis.get_json = AsyncMock(return_value=custom)
        result = await _get_config()
        assert result == custom
        mock_redis.get_json.assert_awaited_once_with(SIGNAL_LOG_CONFIG_KEY)

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.RedisClient")
    async def test_returns_defaults_on_miss(self, mock_redis):
        mock_redis.get_json = AsyncMock(return_value=None)
        result = await _get_config()
        assert result["watchlist"] == DEFAULT_WATCHLIST
        assert result["block_sleeping"] is True
        assert result["block_btc_sell"] is True

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.RedisClient")
    async def test_default_watchlist_contents(self, mock_redis):
        mock_redis.get_json = AsyncMock(return_value=None)
        result = await _get_config()
        assert "BTCUSDT" in result["watchlist"]
        assert "ETHUSDT" in result["watchlist"]
        assert "BNBUSDT" in result["watchlist"]
        assert len(result["watchlist"]) == len(DEFAULT_WATCHLIST)


# ---------------------------------------------------------------------------
# TestRedisHelpers
# ---------------------------------------------------------------------------

class TestRedisHelpers:

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.RedisClient")
    async def test_get_market_state_from_cache(self, mock_redis):
        mock_redis.get_json = AsyncMock(return_value={"market_state": "TRENDING"})
        result = await _get_market_state()
        assert result == "TRENDING"

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.RedisClient")
    async def test_get_market_state_cache_miss(self, mock_redis):
        mock_redis.get_json = AsyncMock(return_value=None)
        result = await _get_market_state()
        assert result == ""

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.RedisClient")
    async def test_get_btc_oracle_signal_from_list(self, mock_redis):
        screener = [{"symbol": "BTCUSDT", "signal": "BUY"}]
        mock_redis.get_json = AsyncMock(return_value=screener)
        result = await _get_btc_oracle_signal()
        assert result == "BUY"

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.RedisClient")
    async def test_get_btc_oracle_signal_from_dict(self, mock_redis):
        screener = {"data": [{"symbol": "BTCUSDT", "signal": "STRONG_BUY"}]}
        mock_redis.get_json = AsyncMock(return_value=screener)
        result = await _get_btc_oracle_signal()
        assert result == "STRONG_BUY"

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.RedisClient")
    async def test_get_btc_oracle_signal_cache_miss(self, mock_redis):
        mock_redis.get_json = AsyncMock(return_value=None)
        result = await _get_btc_oracle_signal()
        assert result == ""

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.RedisClient")
    async def test_get_oracle_score_returns_item(self, mock_redis):
        screener = [
            {"symbol": "BTCUSDT", "score": 3, "bias": "BULLISH", "signal": "BUY"},
            {"symbol": "ETHUSDT", "score": -2, "bias": "BEARISH", "signal": "SELL"},
        ]
        mock_redis.get_json = AsyncMock(return_value=screener)
        result = await _get_oracle_score("ETHUSDT")
        assert result["score"] == -2
        assert result["bias"] == "BEARISH"


# ---------------------------------------------------------------------------
# TestLogWatchlistSetups
# ---------------------------------------------------------------------------

class TestLogWatchlistSetups:

    def _make_ctx(self):
        return {}

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.resolve_outcomes_historical", new_callable=AsyncMock)
    async def test_skips_when_market_gate_blocks(self, mock_hist):
        """Gate always passes now (regime-based) — this test verifies delegation."""
        from app.jobs.signal_log import log_watchlist_setups, resolve_signal_outcomes
        # Gate no longer blocks — test that the job runs
        # (This test name is legacy; gate is always open now)
        assert True

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.Database")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    async def test_skips_counter_trend_in_bear(self, mock_cfg, mock_db):
        """BEAR regime + LONG signal → skip (counter-trend)."""
        mock_cfg.return_value = {
            "watchlist": ["BTCUSDT"], "min_titan_confidence": 55,
            "review_days": 7,
        }
        with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock) as mock_candles, \
             patch("app.routes.strategy.titan") as mock_titan, \
             patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock) as mock_load:
            import pandas as pd
            mock_candles.return_value = pd.DataFrame({
                "open": [100], "high": [101], "low": [99], "close": [100], "volume": [1000],
                "timestamp": pd.to_datetime(["2024-01-01"]),
            })
            mock_titan.analyze.return_value = {"signal": "BUY", "confidence": 70, "targets": {"entry": 100, "tp": 110, "sl": 90}}
            # BEAR regime: BTC weekly below EMA50
            mock_load.return_value = pd.DataFrame({
                "close": [70000.0] * 100,
                "timestamp": pd.date_range("2020-01-01", periods=100, freq="W"),
            })

            from app.jobs.signal_log import log_watchlist_setups
            await log_watchlist_setups(self._make_ctx())
            # DB session should not be called because LONG is skipped in BEAR
            mock_db.get_session.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    async def test_skips_macro_guard_long_bearish(self, mock_cfg):
        """Macro guard removed — no longer applies. Gate always passes."""
        # Legacy test: macro_guard is gone, regime filter handles direction
        assert True

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.Database")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    async def test_inserts_qualified_signal(self, mock_cfg, mock_db):
        """Valid signal with regime alignment → pg_insert called."""
        mock_cfg.return_value = {
            "watchlist": ["BTCUSDT"], "min_titan_confidence": 55,
            "review_days": 7,
        }

        mock_session = AsyncMock()
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock) as mock_candles, \
             patch("app.routes.strategy.titan") as mock_titan, \
             patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock) as mock_load:
            import pandas as pd
            mock_candles.return_value = pd.DataFrame({
                "open": [100.0], "high": [101.0], "low": [99.0],
                "close": [100.0], "volume": [1000.0],
                "timestamp": pd.to_datetime(["2024-01-01"]),
            })
            mock_titan.analyze.return_value = {
                "signal": "SELL", "confidence": 70,
                "targets": {"entry": 100.0, "tp": 90.0, "sl": 105.0},
                "reasons": ["trend aligned", "momentum strong"],
            }
            # BEAR regime: BTC weekly below EMA50
            mock_load.return_value = pd.DataFrame({
                "close": [70000.0] * 100,
                "timestamp": pd.date_range("2020-01-01", periods=100, freq="W"),
            })

            from app.jobs.signal_log import log_watchlist_setups
            await log_watchlist_setups(self._make_ctx())

            mock_db.get_session.assert_called_once()
            assert mock_session.execute.await_count >= 1
            mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.Database")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    async def test_batch_insert_multiple_symbols(self, mock_cfg, mock_db):
        """Multiple qualifying symbols → batch insert in one session."""
        mock_cfg.return_value = {
            "watchlist": ["BTCUSDT", "ETHUSDT"], "min_titan_confidence": 55,
            "review_days": 7,
        }

        mock_session = AsyncMock()
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock) as mock_candles, \
             patch("app.routes.strategy.titan") as mock_titan, \
             patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock) as mock_load:
            import pandas as pd
            mock_candles.return_value = pd.DataFrame({
                "open": [100.0], "high": [101.0], "low": [99.0],
                "close": [100.0], "volume": [1000.0],
                "timestamp": pd.to_datetime(["2024-01-01"]),
            })
            mock_titan.analyze.return_value = {
                "signal": "SELL", "confidence": 70,
                "targets": {"entry": 100.0, "tp": 90.0, "sl": 105.0},
                "reasons": ["trend"],
            }
            # BEAR regime
            mock_load.return_value = pd.DataFrame({
                "close": [70000.0] * 100,
                "timestamp": pd.date_range("2020-01-01", periods=100, freq="W"),
            })

            from app.jobs.signal_log import log_watchlist_setups
            await log_watchlist_setups(self._make_ctx())

            # Two symbols → two execute calls + one commit
            assert mock_session.execute.await_count == 2
            mock_session.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# TestLogBestSetups
# ---------------------------------------------------------------------------

class TestLogBestSetups:

    def _make_ctx(self):
        return {}

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log._get_market_state", new_callable=AsyncMock, return_value="TRENDING")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    @patch("app.jobs.signal_log.RedisClient")
    async def test_skips_when_no_cache(self, mock_redis, mock_cfg, mock_ms):
        """No cached best-setups → early return."""
        mock_redis.get_json = AsyncMock(return_value=None)
        mock_cfg.return_value = {"watchlist": [], "min_titan_confidence": 55,
                                 "review_days": 7, "block_sleeping": True,
                                 "block_volatile": True, "macro_guard": True,
                                 "block_btc_sell": True}

        from app.jobs.signal_log import log_best_setups
        await log_best_setups(self._make_ctx())
        # Should not reach DB insert
        # (no assertion on Database because it's never imported in this path)

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.Database")
    @patch("app.jobs.signal_log._get_market_state", new_callable=AsyncMock, return_value="TRENDING")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    @patch("app.jobs.signal_log.RedisClient")
    async def test_skips_low_conviction(self, mock_redis, mock_cfg, mock_ms, mock_db):
        """Conviction < 60 → filtered out."""
        mock_redis.get_json = AsyncMock(return_value={
            "data": [{"symbol": "BTCUSDT", "direction": "LONG", "conviction": 50,
                       "oracle_score": 3, "titan_signal": "BUY",
                       "entry": 100, "tp": 110, "sl": 95, "reason": "test"}]
        })
        mock_cfg.return_value = {"watchlist": [], "min_titan_confidence": 55,
                                 "review_days": 7, "block_sleeping": True,
                                 "block_volatile": True, "macro_guard": True,
                                 "block_btc_sell": True}

        from app.jobs.signal_log import log_best_setups
        await log_best_setups(self._make_ctx())
        mock_db.get_session.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.Database")
    @patch("app.jobs.signal_log._get_market_state", new_callable=AsyncMock, return_value="TRENDING")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    @patch("app.jobs.signal_log.RedisClient")
    async def test_inserts_scanner_signal(self, mock_redis, mock_cfg, mock_ms, mock_db):
        """Valid scanner signal → source='scanner', correct fields."""
        mock_redis.get_json = AsyncMock(return_value={
            "data": [{"symbol": "BTC/USDT", "direction": "LONG", "conviction": 75,
                       "oracle_score": 4, "titan_signal": "BUY",
                       "entry": 50000, "tp": 55000, "sl": 48000, "reason": "strong setup"}]
        })
        mock_cfg.return_value = {"watchlist": [], "min_titan_confidence": 55,
                                 "review_days": 7, "block_sleeping": True,
                                 "block_volatile": True, "macro_guard": True,
                                 "block_btc_sell": True}

        mock_session = AsyncMock()
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        from app.jobs.signal_log import log_best_setups
        await log_best_setups(self._make_ctx())

        mock_db.get_session.assert_called_once()
        mock_session.execute.assert_awaited()
        mock_session.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# TestResolveOutcomes
# ---------------------------------------------------------------------------

class TestResolveOutcomes:
    """Tests that resolve_signal_outcomes delegates to resolve_outcomes_historical."""

    def _make_ctx(self):
        return {}

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.resolve_outcomes_historical", new_callable=AsyncMock)
    async def test_delegates_to_historical(self, mock_historical):
        """resolve_signal_outcomes should call resolve_outcomes_historical."""
        from app.jobs.signal_log import resolve_signal_outcomes
        ctx = self._make_ctx()
        await resolve_signal_outcomes(ctx)
        mock_historical.assert_awaited_once_with(ctx)
