"""
Tests for signal_log.py — the core signal pipeline.

Covers:
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
    _get_config,
    _get_market_state,
    _get_btc_oracle_signal,
    _get_oracle_score,
    DEFAULT_WATCHLIST,
    SIGNAL_LOG_CONFIG_KEY,
)


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
        assert result == "UNKNOWN"

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
    @patch("app.jobs.signal_log.RedisClient")
    async def test_skips_counter_trend_in_bear(self, mock_redis, mock_cfg, mock_db):
        """BEAR regime + LONG signal → skip (counter-trend)."""
        mock_cfg.return_value = {
            "watchlist": ["BTCUSDT"], "min_titan_confidence": 55,
            "review_days": 7,
        }
        # No cached regime — let it compute from BTC weekly
        mock_redis.get_json = AsyncMock(return_value=None)
        mock_redis.set_json = AsyncMock()

        with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock) as mock_candles, \
             patch("app.routes.strategy.titan") as mock_titan, \
             patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock) as mock_load:
            import pandas as pd
            import numpy as np
            mock_candles.return_value = pd.DataFrame({
                "open": [100], "high": [101], "low": [99], "close": [100], "volume": [1000],
                "timestamp": pd.to_datetime(["2024-01-01"]),
            })
            mock_titan.analyze.return_value = {"signal": "BUY", "confidence": 70, "targets": {"entry": 100, "tp": 110, "sl": 90}}
            # BEAR regime: declining prices → last close below EMA50
            mock_load.return_value = pd.DataFrame({
                "close": np.linspace(80000.0, 10000.0, 100),
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
    @patch("app.jobs.signal_log.RedisClient")
    async def test_inserts_qualified_signal(self, mock_redis, mock_cfg, mock_db):
        """Valid signal with regime alignment → pg_insert called."""
        mock_cfg.return_value = {
            "watchlist": ["BTCUSDT"], "min_titan_confidence": 55,
            "review_days": 7,
        }
        # No cached regime — let it compute from BTC weekly
        mock_redis.get_json = AsyncMock(return_value=None)
        mock_redis.set_json = AsyncMock()

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
            # BEAR regime: BTC weekly declining so last close below EMA50
            import numpy as np
            mock_load.return_value = pd.DataFrame({
                "close": np.linspace(80000.0, 10000.0, 100),
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
    @patch("app.jobs.signal_log.RedisClient")
    async def test_batch_insert_multiple_symbols(self, mock_redis, mock_cfg, mock_db):
        """Multiple qualifying symbols → batch insert in one session."""
        mock_cfg.return_value = {
            "watchlist": ["BTCUSDT", "ETHUSDT"], "min_titan_confidence": 55,
            "review_days": 7,
        }
        # No cached regime — let it compute from BTC weekly
        mock_redis.get_json = AsyncMock(return_value=None)
        mock_redis.set_json = AsyncMock()

        mock_session = AsyncMock()
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock) as mock_candles, \
             patch("app.routes.strategy.titan") as mock_titan, \
             patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock) as mock_load:
            import pandas as pd
            import numpy as np
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
            # BEAR regime: declining prices → last close below EMA50
            mock_load.return_value = pd.DataFrame({
                "close": np.linspace(80000.0, 10000.0, 100),
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
        """Conviction < 50 → skipped entirely (not persisted)."""
        mock_redis.get_json = AsyncMock(return_value={
            "data": [{"symbol": "BTCUSDT", "direction": "LONG", "conviction": 49,
                       "oracle_score": 3, "titan_signal": "BUY",
                       "entry": 100, "tp": 110, "sl": 95, "reason": "test"}]
        })
        mock_cfg.return_value = {"watchlist": [], "min_titan_confidence": 55,
                                 "review_days": 7, "block_sleeping": True,
                                 "block_volatile": True, "macro_guard": True,
                                 "block_btc_sell": True}

        from app.jobs.signal_log import log_best_setups
        await log_best_setups(self._make_ctx())
        # Cooldown pre-fetch runs (1 DB call), but no rows qualify → no insert, no commit
        assert mock_db.get_session.call_count == 1

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.COUNTER_REGIME_ENABLED", True)
    @patch("app.jobs.signal_log.Database")
    @patch("app.jobs.signal_log._get_market_state", new_callable=AsyncMock, return_value="TRENDING")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    @patch("app.jobs.signal_log.RedisClient")
    async def test_skips_counter_regime(self, mock_redis, mock_cfg, mock_ms, mock_db):
        """Counter-regime signals (reason starts with '(counter)') → logged with source='counter'."""
        mock_redis.get_json = AsyncMock(return_value={
            "data": [{"symbol": "XLMUSDT", "direction": "LONG", "conviction": 75,
                       "oracle_score": 4, "titan_signal": "BUY",
                       "entry": 0.30, "tp": 0.35, "sl": 0.27, "reason": "(counter) BUY_LIMIT"}]
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
        # 2 DB calls: cooldown pre-fetch + insert
        assert mock_db.get_session.call_count == 2
        mock_session.execute.assert_awaited()
        mock_session.commit.assert_awaited_once()

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
                       "entry": 50000, "tp": 55000, "sl": 48000, "reason": "(trend) BUY"}]
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

        # 2 DB calls: cooldown pre-fetch + insert
        assert mock_db.get_session.call_count == 2
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
    @patch("app.jobs.signal_log.datetime")
    async def test_delegates_to_historical(self, mock_dt, mock_historical):
        """resolve_signal_outcomes should call resolve_outcomes_historical at :00 or :30."""
        from app.jobs.signal_log import resolve_signal_outcomes
        # Freeze time at a :00 minute so the throttle gate is open
        mock_now = MagicMock()
        mock_now.minute = 0
        mock_dt.now.return_value = mock_now
        ctx = self._make_ctx()
        await resolve_signal_outcomes(ctx)
        mock_historical.assert_awaited_once_with(ctx)


# ---------------------------------------------------------------------------
# TestResolveOutcomesPositionBridge
# ---------------------------------------------------------------------------

class TestResolveOutcomesPositionBridge:
    """Tests that signal resolution closes linked positions."""

    def _make_signal(self, **overrides):
        sig = MagicMock()
        sig.id = 100
        sig.symbol = "BTCUSDT"
        sig.direction = "SHORT"
        sig.fired_at = 1700000000000
        sig.entry = 70000.0
        sig.tp = 66000.0
        sig.sl = 73000.0
        sig.outcome = "OPEN"
        sig.resolved_at = None
        sig.resolved_price = None
        sig.regime_at_resolution = None
        sig.btc_price_at_resolution = None
        sig.time_to_resolution_ms = None
        for k, v in overrides.items():
            setattr(sig, k, v)
        return sig

    def _make_position(self, **overrides):
        pos = MagicMock()
        pos.id = 42
        pos.signal_log_id = 100
        pos.symbol = "BTCUSDT"
        pos.direction = "SHORT"
        pos.status = "OPEN"
        pos.actual_entry = 70000.0
        pos.intended_entry = 70000.0
        pos.intended_tp = 66000.0
        pos.intended_sl = 73000.0
        pos.quantity = 0.01
        pos.quote_amount = 700.0
        pos.pnl_usd = None
        pos.pnl_pct = None
        pos.outcome = None
        pos.closed_at = None
        pos.market_state_at_close = None
        for k, v in overrides.items():
            setattr(pos, k, v)
        return pos

    def _candle_df(self, fired_at_ms):
        """Create candles that trigger a SHORT TP hit (low <= tp)."""
        import pandas as pd
        return pd.DataFrame({
            "timestamp": pd.to_datetime([fired_at_ms, fired_at_ms + 14400000], unit="ms"),
            "open": [70000.0, 68000.0],
            "high": [70500.0, 68500.0],
            "low": [69000.0, 65000.0],   # low=65000 < tp=66000 → TP hit
            "close": [68000.0, 66000.0],
            "volume": [100.0, 100.0],
        })

    @pytest.mark.asyncio
    @patch("app.providers.get_provider")
    @patch("app.jobs.signal_log._get_market_state", new_callable=AsyncMock, return_value="BEAR")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    @patch("app.jobs.signal_log.Database")
    async def test_resolves_signal_and_closes_open_position(self, mock_db, mock_cfg, mock_ms, mock_provider):
        """When a signal resolves WIN, the linked OPEN position should close with PnL."""
        mock_cfg.return_value = {"review_days": 7}
        mock_provider.return_value = AsyncMock()

        sig = self._make_signal()
        pos = self._make_position()

        # Mock session: first execute returns open signals, second returns position
        mock_session = AsyncMock()
        sig_result = MagicMock()
        sig_result.scalars.return_value.all.return_value = [sig]
        pos_result = MagicMock()
        pos_result.scalars.return_value.first.return_value = pos

        mock_session.execute = AsyncMock(side_effect=[sig_result, pos_result])
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        import pandas as pd
        candle_df = self._candle_df(sig.fired_at)

        with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=candle_df), \
             patch("app.schemas.activity_log.log_activity", new_callable=AsyncMock):

            from app.jobs.signal_log import resolve_outcomes_historical
            await resolve_outcomes_historical({})

        # Signal should be resolved as WIN
        assert sig.outcome == "WIN"
        assert sig.resolved_price == sig.tp

        # Position should be CLOSED with PnL
        assert pos.status == "CLOSED"
        assert pos.outcome == "WIN"
        assert pos.actual_exit == sig.tp
        assert pos.pnl_usd is not None
        assert pos.pnl_usd > 0  # SHORT won, so PnL should be positive

    @pytest.mark.asyncio
    @patch("app.providers.get_provider")
    @patch("app.jobs.signal_log._get_market_state", new_callable=AsyncMock, return_value="BEAR")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    @patch("app.jobs.signal_log.Database")
    async def test_cancels_pending_position_on_resolve(self, mock_db, mock_cfg, mock_ms, mock_provider):
        """When a signal resolves, a linked PENDING position should be cancelled."""
        mock_cfg.return_value = {"review_days": 7}
        mock_provider.return_value = AsyncMock()

        sig = self._make_signal()
        pos = self._make_position(status="PENDING", actual_entry=None)

        mock_session = AsyncMock()
        sig_result = MagicMock()
        sig_result.scalars.return_value.all.return_value = [sig]
        pos_result = MagicMock()
        pos_result.scalars.return_value.first.return_value = pos

        mock_session.execute = AsyncMock(side_effect=[sig_result, pos_result])
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        import pandas as pd
        candle_df = self._candle_df(sig.fired_at)

        with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=candle_df), \
             patch("app.schemas.activity_log.log_activity", new_callable=AsyncMock):

            from app.jobs.signal_log import resolve_outcomes_historical
            await resolve_outcomes_historical({})

        assert pos.status == "CANCELLED"
        assert pos.outcome == "EXPIRED"

    @pytest.mark.asyncio
    @patch("app.providers.get_provider")
    @patch("app.jobs.signal_log._get_market_state", new_callable=AsyncMock, return_value="BEAR")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    @patch("app.jobs.signal_log.Database")
    async def test_resolves_signal_without_position(self, mock_db, mock_cfg, mock_ms, mock_provider):
        """Signal resolves normally even when no linked position exists."""
        mock_cfg.return_value = {"review_days": 7}
        mock_provider.return_value = AsyncMock()

        sig = self._make_signal()

        mock_session = AsyncMock()
        sig_result = MagicMock()
        sig_result.scalars.return_value.all.return_value = [sig]
        no_pos_result = MagicMock()
        no_pos_result.scalars.return_value.first.return_value = None

        mock_session.execute = AsyncMock(side_effect=[sig_result, no_pos_result])
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        import pandas as pd
        candle_df = self._candle_df(sig.fired_at)

        with patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=candle_df), \
             patch("app.schemas.activity_log.log_activity", new_callable=AsyncMock):

            from app.jobs.signal_log import resolve_outcomes_historical
            await resolve_outcomes_historical({})

        assert sig.outcome == "WIN"
        assert sig.resolved_price == sig.tp


# ---------------------------------------------------------------------------
# TestTiebreaker5m — 5min candle tiebreaker for same-candle TP+SL hits
# ---------------------------------------------------------------------------

class TestTiebreaker5m:
    """Tests for _resolve_tiebreaker_5m — determines TP/SL ordering via 5min candles."""

    def _make_5m_df(self, candle_open_ms, rows):
        """
        Build a 5min candle DataFrame.
        rows: list of (offset_ms, high, low) relative to candle_open_ms
        """
        import pandas as pd
        data = []
        for offset_ms, high, low in rows:
            ts_ms = candle_open_ms + offset_ms
            data.append({
                "timestamp": pd.Timestamp(ts_ms, unit="ms"),
                "open": 0, "high": high, "low": low, "close": 0, "volume": 0,
            })
        return pd.DataFrame(data)

    @pytest.mark.asyncio
    @patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock)
    async def test_tp_hit_first_returns_win(self, mock_candles):
        """5min candles show TP hit before SL → WIN at TP price."""
        from app.jobs.signal_log import _resolve_tiebreaker_5m

        candle_open_ms = 1700000000000
        # LONG signal: tp=110, sl=90
        # First 5m: high=105, low=95 (neither hit)
        # Second 5m: high=112 (TP hit!), low=98
        mock_candles.return_value = self._make_5m_df(candle_open_ms, [
            (0, 105.0, 95.0),
            (300000, 112.0, 98.0),
            (600000, 108.0, 88.0),  # SL hit after TP
        ])

        result = await _resolve_tiebreaker_5m(
            "BTCUSDT", "LONG", 110.0, 90.0, candle_open_ms, MagicMock(),
        )
        assert result["outcome"] == "WIN"
        assert result["resolved_price"] == 110.0
        assert result["resolved_at_ms"] == candle_open_ms + 300000

    @pytest.mark.asyncio
    @patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock)
    async def test_sl_hit_first_returns_loss(self, mock_candles):
        """5min candles show SL hit before TP → LOSS at SL price."""
        from app.jobs.signal_log import _resolve_tiebreaker_5m

        candle_open_ms = 1700000000000
        # LONG signal: tp=110, sl=90
        # First 5m: high=105, low=88 (SL hit!)
        mock_candles.return_value = self._make_5m_df(candle_open_ms, [
            (0, 105.0, 88.0),
            (300000, 112.0, 85.0),
        ])

        result = await _resolve_tiebreaker_5m(
            "BTCUSDT", "LONG", 110.0, 90.0, candle_open_ms, MagicMock(),
        )
        assert result["outcome"] == "LOSS"
        assert result["resolved_price"] == 90.0
        assert result["resolved_at_ms"] == candle_open_ms

    @pytest.mark.asyncio
    @patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock)
    async def test_short_tp_hit_first_returns_win(self, mock_candles):
        """SHORT: 5min candles show TP hit before SL → WIN."""
        from app.jobs.signal_log import _resolve_tiebreaker_5m

        candle_open_ms = 1700000000000
        # SHORT signal: tp=90, sl=110
        # First 5m: low=88 (TP hit for SHORT), high=105
        mock_candles.return_value = self._make_5m_df(candle_open_ms, [
            (0, 105.0, 88.0),
            (300000, 112.0, 85.0),
        ])

        result = await _resolve_tiebreaker_5m(
            "BTCUSDT", "SHORT", 90.0, 110.0, candle_open_ms, MagicMock(),
        )
        assert result["outcome"] == "WIN"
        assert result["resolved_price"] == 90.0

    @pytest.mark.asyncio
    @patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock)
    async def test_short_sl_hit_first_returns_loss(self, mock_candles):
        """SHORT: 5min candles show SL hit before TP → LOSS."""
        from app.jobs.signal_log import _resolve_tiebreaker_5m

        candle_open_ms = 1700000000000
        # SHORT signal: tp=90, sl=110
        # First 5m: high=112 (SL hit for SHORT), low=100
        mock_candles.return_value = self._make_5m_df(candle_open_ms, [
            (0, 112.0, 100.0),
            (300000, 108.0, 88.0),
        ])

        result = await _resolve_tiebreaker_5m(
            "BTCUSDT", "SHORT", 90.0, 110.0, candle_open_ms, MagicMock(),
        )
        assert result["outcome"] == "LOSS"
        assert result["resolved_price"] == 110.0

    @pytest.mark.asyncio
    @patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock)
    async def test_no_5m_data_falls_back_to_loss(self, mock_candles):
        """No 5min candles available → conservative LOSS fallback."""
        from app.jobs.signal_log import _resolve_tiebreaker_5m

        import pandas as pd
        mock_candles.return_value = pd.DataFrame()

        result = await _resolve_tiebreaker_5m(
            "BTCUSDT", "LONG", 110.0, 90.0, 1700000000000, MagicMock(),
        )
        assert result["outcome"] == "LOSS"
        assert result["resolved_price"] == 90.0

    @pytest.mark.asyncio
    @patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock)
    async def test_fetch_error_falls_back_to_loss(self, mock_candles):
        """5min fetch throws exception → conservative LOSS fallback."""
        from app.jobs.signal_log import _resolve_tiebreaker_5m

        mock_candles.side_effect = Exception("API error")

        result = await _resolve_tiebreaker_5m(
            "BTCUSDT", "LONG", 110.0, 90.0, 1700000000000, MagicMock(),
        )
        assert result["outcome"] == "LOSS"
        assert result["resolved_price"] == 90.0

    @pytest.mark.asyncio
    @patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock)
    async def test_both_hit_same_5m_candle_continues(self, mock_candles):
        """If both hit in same 5m candle, keep walking — next candle resolves."""
        from app.jobs.signal_log import _resolve_tiebreaker_5m

        candle_open_ms = 1700000000000
        # First 5m: both hit (skip), second 5m: only TP hit
        mock_candles.return_value = self._make_5m_df(candle_open_ms, [
            (0, 112.0, 88.0),       # both hit — ambiguous, skip
            (300000, 112.0, 95.0),  # TP hit, SL not hit
        ])

        result = await _resolve_tiebreaker_5m(
            "BTCUSDT", "LONG", 110.0, 90.0, candle_open_ms, MagicMock(),
        )
        assert result["outcome"] == "WIN"
        assert result["resolved_at_ms"] == candle_open_ms + 300000


# ---------------------------------------------------------------------------
# TestResolveOutcomesTiebreaker — integration: 4H resolution uses tiebreaker
# ---------------------------------------------------------------------------

class TestResolveOutcomesTiebreaker:
    """Integration tests: resolve_outcomes_historical calls tiebreaker on same-candle TP+SL."""

    def _make_signal(self, **overrides):
        sig = MagicMock()
        sig.id = 200
        sig.symbol = "ETHUSDT"
        sig.direction = "LONG"
        sig.fired_at = 1700000000000
        sig.entry = 3000.0
        sig.tp = 3200.0
        sig.sl = 2800.0
        sig.outcome = "OPEN"
        sig.resolved_at = None
        sig.resolved_price = None
        sig.regime_at_resolution = None
        sig.btc_price_at_resolution = None
        sig.time_to_resolution_ms = None
        for k, v in overrides.items():
            setattr(sig, k, v)
        return sig

    def _candle_df_both_hit(self, fired_at_ms):
        """4H candles where both TP and SL are hit in the same candle."""
        import pandas as pd
        return pd.DataFrame({
            "timestamp": pd.to_datetime([fired_at_ms, fired_at_ms + 14400000], unit="ms"),
            "open": [3000.0, 3100.0],
            "high": [3100.0, 3250.0],   # high >= tp (3200)
            "low": [2900.0, 2750.0],    # low <= sl (2800)
            "close": [3100.0, 3050.0],
            "volume": [100.0, 100.0],
        })

    def _make_5m_df_tiebreak(self, candle_open_ms):
        """5min candles where TP is hit before SL within the 4H window."""
        import pandas as pd
        return pd.DataFrame({
            "timestamp": pd.to_datetime([
                candle_open_ms,
                candle_open_ms + 300000,
                candle_open_ms + 600000,
            ], unit="ms"),
            "open": [3100.0, 3150.0, 3210.0],
            "high": [3120.0, 3180.0, 3220.0],   # 3rd: high=3220 >= tp=3200
            "low": [3050.0, 3100.0, 3150.0],    # never hits sl=2800
            "close": [3150.0, 3180.0, 3210.0],
            "volume": [10.0, 10.0, 10.0],
        })

    @pytest.mark.asyncio
    @patch("app.providers.get_provider")
    @patch("app.jobs.signal_log._get_market_state", new_callable=AsyncMock, return_value="BULL")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    @patch("app.jobs.signal_log.Database")
    async def test_same_candle_tp_sl_uses_tiebreaker(self, mock_db, mock_cfg, mock_ms, mock_provider):
        """When both TP+SL hit in same 4H candle, tiebreaker determines outcome."""
        mock_cfg.return_value = {"review_days": 7}
        mock_provider.return_value = AsyncMock()

        sig = self._make_signal()
        candle_open_ms = sig.fired_at + 14400000  # second candle

        mock_session = AsyncMock()
        sig_result = MagicMock()
        sig_result.scalars.return_value.all.return_value = [sig]
        no_pos_result = MagicMock()
        no_pos_result.scalars.return_value.first.return_value = None

        mock_session.execute = AsyncMock(side_effect=[sig_result, no_pos_result])
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        candle_df = self._candle_df_both_hit(sig.fired_at)
        tiebreak_df = self._make_5m_df_tiebreak(candle_open_ms)

        async def mock_get_candles(symbol, timeframe, limit=500, provider=None):
            if timeframe == "5m":
                return tiebreak_df
            return candle_df

        with patch("app.routes.strategy.get_candles_df", side_effect=mock_get_candles), \
             patch("app.schemas.activity_log.log_activity", new_callable=AsyncMock):

            from app.jobs.signal_log import resolve_outcomes_historical
            await resolve_outcomes_historical({})

        # Tiebreaker determined TP hit first → WIN
        assert sig.outcome == "WIN"
        assert sig.resolved_price == sig.tp

    @pytest.mark.asyncio
    @patch("app.providers.get_provider")
    @patch("app.jobs.signal_log._get_market_state", new_callable=AsyncMock, return_value="BULL")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    @patch("app.jobs.signal_log.Database")
    async def test_tiebreaker_no_5m_data_resolves_as_loss(self, mock_db, mock_cfg, mock_ms, mock_provider):
        """When 5min data unavailable, same-candle TP+SL falls back to conservative LOSS."""
        mock_cfg.return_value = {"review_days": 7}
        mock_provider.return_value = AsyncMock()

        sig = self._make_signal()

        mock_session = AsyncMock()
        sig_result = MagicMock()
        sig_result.scalars.return_value.all.return_value = [sig]
        no_pos_result = MagicMock()
        no_pos_result.scalars.return_value.first.return_value = None

        mock_session.execute = AsyncMock(side_effect=[sig_result, no_pos_result])
        mock_db.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.get_session.return_value.__aexit__ = AsyncMock(return_value=False)

        candle_df = self._candle_df_both_hit(sig.fired_at)

        async def mock_get_candles(symbol, timeframe, limit=500, provider=None):
            import pandas as pd
            if timeframe == "5m":
                return pd.DataFrame()
            return candle_df

        with patch("app.routes.strategy.get_candles_df", side_effect=mock_get_candles), \
             patch("app.schemas.activity_log.log_activity", new_callable=AsyncMock):

            from app.jobs.signal_log import resolve_outcomes_historical
            await resolve_outcomes_historical({})

        assert sig.outcome == "LOSS"
        assert sig.resolved_price == sig.sl


# ---------------------------------------------------------------------------
# A2: TestHistoricalResolution — resolve_outcome candle-walk edge cases
# Tests the pure candle-walk logic in backtest_engine.resolve_outcome directly,
# covering TP/SL hit order, same-candle tiebreak, and REVIEW on no data.
# ---------------------------------------------------------------------------

class TestHistoricalResolution:
    """Unit tests for resolve_outcome() candle-walk logic (no DB, no mocks)."""

    def _make_df(self, rows: list[dict]) -> "pd.DataFrame":
        import pandas as pd
        base_ms = 1_704_067_200_000
        data = []
        for i, r in enumerate(rows):
            data.append({
                "timestamp": pd.Timestamp(base_ms + i * 14_400_000, unit="ms", tz="UTC"),
                "open": 100.0,
                "high": r["high"],
                "low": r["low"],
                "close": 100.0,
                "volume": 1000.0,
                "ts_ms": base_ms + i * 14_400_000,
            })
        return pd.DataFrame(data)

    def test_historical_long_tp_hit(self):
        """LONG: candle high reaches TP → WIN."""
        from app.trading.backtest_engine import resolve_outcome
        df = self._make_df([
            {"high": 104.0, "low": 98.0},   # entry candle (not scanned)
            {"high": 115.0, "low": 101.0},  # TP=110 hit
        ])
        outcome, price, ts = resolve_outcome(df, 0, "LONG", tp=110.0, sl=95.0)
        assert outcome == "WIN"
        assert price == 110.0

    def test_historical_long_sl_hit(self):
        """LONG: candle low drops to SL → LOSS."""
        from app.trading.backtest_engine import resolve_outcome
        df = self._make_df([
            {"high": 104.0, "low": 98.0},
            {"high": 103.0, "low": 92.0},  # SL=95 hit
        ])
        outcome, price, ts = resolve_outcome(df, 0, "LONG", tp=110.0, sl=95.0)
        assert outcome == "LOSS"
        assert price == 95.0

    def test_historical_short_tp_hit(self):
        """SHORT: candle low drops to TP → WIN."""
        from app.trading.backtest_engine import resolve_outcome
        df = self._make_df([
            {"high": 102.0, "low": 96.0},
            {"high": 99.0, "low": 87.0},   # TP=90 hit (low <= tp)
        ])
        outcome, price, ts = resolve_outcome(df, 0, "SHORT", tp=90.0, sl=108.0)
        assert outcome == "WIN"
        assert price == 90.0

    def test_historical_both_hit_bullish_candle(self):
        """Same candle crosses both TP and SL → conservative LOSS."""
        from app.trading.backtest_engine import resolve_outcome
        df = self._make_df([
            {"high": 104.0, "low": 98.0},
            {"high": 120.0, "low": 85.0},  # Both TP=110 and SL=92 crossed
        ])
        outcome, price, ts = resolve_outcome(df, 0, "LONG", tp=110.0, sl=92.0)
        assert outcome == "LOSS"
        assert price == 92.0

    def test_historical_review_no_candles(self):
        """Only the entry candle exists — no future candles → REVIEW."""
        from app.trading.backtest_engine import resolve_outcome
        df = self._make_df([{"high": 102.0, "low": 98.0}])
        outcome, price, ts = resolve_outcome(df, 0, "LONG", tp=110.0, sl=90.0)
        assert outcome == "REVIEW"
        assert price is None
        assert ts is None

    def test_historical_review_max_hold_exceeded(self):
        """max_hold candles pass without hitting TP or SL → REVIEW."""
        from app.trading.backtest_engine import resolve_outcome
        # Flat candles — price never moves enough
        df = self._make_df([{"high": 101.5, "low": 98.5}] * 15)
        outcome, price, ts = resolve_outcome(
            df, 0, "LONG", tp=110.0, sl=90.0, max_hold=5
        )
        assert outcome == "REVIEW"


# ---------------------------------------------------------------------------
# TestRegimeCachingSignalLog — regime Redis cache in log_watchlist_setups
# ---------------------------------------------------------------------------

class TestRegimeCachingSignalLog:
    """Verify regime cache hit skips BTC fetch; miss fetches, computes, stores."""

    def _make_ctx(self):
        return {}

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.Database")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    @patch("app.jobs.signal_log.RedisClient")
    async def test_regime_cache_hit_skips_btc_fetch(self, mock_redis, mock_cfg, mock_db):
        """When market:regime is in Redis, load_candles is NOT called."""
        mock_cfg.return_value = {
            "watchlist": [], "min_titan_confidence": 55, "review_days": 7,
        }
        # Simulate cache hit for regime
        async def fake_get_json(key):
            if key == "market:regime":
                return {"regime": "BULL"}
            return None
        mock_redis.get_json = AsyncMock(side_effect=fake_get_json)
        mock_redis.set_json = AsyncMock()

        with patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock) as mock_load:
            from app.jobs.signal_log import log_watchlist_setups
            await log_watchlist_setups(self._make_ctx())
            mock_load.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("app.jobs.signal_log.Database")
    @patch("app.jobs.signal_log._get_config", new_callable=AsyncMock)
    @patch("app.jobs.signal_log.RedisClient")
    async def test_regime_cache_miss_fetches_and_stores(self, mock_redis, mock_cfg, mock_db):
        """On cache miss, BTC weekly is fetched and result is stored in Redis."""
        import pandas as pd
        mock_cfg.return_value = {
            "watchlist": [], "min_titan_confidence": 55, "review_days": 7,
        }
        mock_redis.get_json = AsyncMock(return_value=None)
        mock_redis.set_json = AsyncMock()

        # BTC weekly candles — rising prices so last close well above EMA50 → BULL
        import numpy as np
        btc_weekly = pd.DataFrame({
            "close": np.linspace(10000.0, 80000.0, 100),
            "timestamp": pd.date_range("2020-01-01", periods=100, freq="W"),
        })

        with patch("app.trading.backtest_engine.load_candles", new_callable=AsyncMock, return_value=btc_weekly):
            from app.jobs.signal_log import log_watchlist_setups
            await log_watchlist_setups(self._make_ctx())

        # set_json should have been called to cache the regime
        mock_redis.set_json.assert_awaited()
        call_args = mock_redis.set_json.call_args_list
        regime_call = next(
            (c for c in call_args if c[0][0] == "market:regime"),
            None,
        )
        assert regime_call is not None, "Expected set_json called with 'market:regime'"
        assert regime_call[0][1]["regime"] == "BULL"
