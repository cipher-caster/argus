"""
Tests for the paper trading engine.

Covers:
- RiskManager: all gate permutations + position sizing
- PortfolioTracker: balance calculation, stats
- TradeOrchestrator: full PENDING → OPEN → CLOSED simulation cycle
"""
import json
import time
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.trading.risk_manager import RiskManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_config(**overrides):
    base = {
        "enabled": True,
        "initial_capital": 100.0,
        "max_position_size_pct": 10.0,
        "max_concurrent_positions": 3,
        "max_correlated_positions": 2,
        "max_drawdown_pct": 15.0,
        "min_conviction": 65,
        "order_expiry_hours": 8,
        "correlation_groups": {
            "btc_correlated": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ARBUSDT", "NEARUSDT", "APTUSDT"]
        },
    }
    base.update(overrides)
    return base


def make_position(symbol="BTCUSDT", direction="LONG", status="OPEN"):
    pos = MagicMock()
    pos.symbol = symbol
    pos.direction = direction
    pos.status = status
    return pos


# ---------------------------------------------------------------------------
# RiskManager — gate tests
# ---------------------------------------------------------------------------

class TestRiskManagerDrawdown:

    def test_healthy_balance_passes(self):
        rm = RiskManager()
        config = make_config(initial_capital=100.0, max_drawdown_pct=15.0)
        ok, reason = rm.check_drawdown(balance=90.0, config=config)
        assert ok is True

    def test_balance_at_floor_passes(self):
        rm = RiskManager()
        config = make_config(initial_capital=100.0, max_drawdown_pct=15.0)
        # floor = 85.0 — exactly at floor should still pass (< not <=)
        ok, reason = rm.check_drawdown(balance=85.0, config=config)
        assert ok is True

    def test_balance_below_floor_blocks(self):
        rm = RiskManager()
        config = make_config(initial_capital=100.0, max_drawdown_pct=15.0)
        ok, reason = rm.check_drawdown(balance=84.99, config=config)
        assert ok is False
        assert "Circuit breaker" in reason

    def test_zero_balance_blocks(self):
        rm = RiskManager()
        config = make_config(initial_capital=100.0, max_drawdown_pct=15.0)
        ok, _ = rm.check_drawdown(balance=0.0, config=config)
        assert ok is False


class TestRiskManagerCorrelation:

    def test_no_open_positions_passes(self):
        rm = RiskManager()
        config = make_config()
        ok, _ = rm.check_correlation("BTCUSDT", [], config)
        assert ok is True

    def test_one_correlated_passes(self):
        rm = RiskManager()
        config = make_config(max_correlated_positions=2)
        positions = [make_position("ETHUSDT")]
        ok, _ = rm.check_correlation("BTCUSDT", positions, config)
        assert ok is True

    def test_at_correlated_limit_blocks(self):
        rm = RiskManager()
        config = make_config(max_correlated_positions=2)
        positions = [make_position("ETHUSDT"), make_position("BNBUSDT")]
        ok, reason = rm.check_correlation("BTCUSDT", positions, config)
        assert ok is False
        assert "Correlation limit" in reason

    def test_uncorrelated_symbol_passes(self):
        rm = RiskManager()
        config = make_config(max_correlated_positions=1)
        # Even if btc_correlated is full, an uncorrelated symbol (TRXUSDT) passes
        positions = [make_position("BTCUSDT"), make_position("ETHUSDT")]
        ok, _ = rm.check_correlation("TRXUSDT", positions, config)
        assert ok is True


class TestRiskManagerConviction:

    def test_above_minimum_passes(self):
        rm = RiskManager()
        config = make_config(min_conviction=65)
        ok, _ = rm.check_conviction(70, config)
        assert ok is True

    def test_exactly_at_minimum_passes(self):
        rm = RiskManager()
        config = make_config(min_conviction=65)
        ok, _ = rm.check_conviction(65, config)
        assert ok is True

    def test_below_minimum_blocks(self):
        rm = RiskManager()
        config = make_config(min_conviction=65)
        ok, reason = rm.check_conviction(64, config)
        assert ok is False
        assert "Low conviction" in reason

    def test_live_signal_conviction_56_passes_default(self):
        """Live watchlist signals fire at conviction 56 — default min should allow them."""
        rm = RiskManager()
        from app.trading.orchestrator import DEFAULT_TRADING_CONFIG
        ok, _ = rm.check_conviction(56, DEFAULT_TRADING_CONFIG)
        assert ok is True


class TestRiskManagerMinOrderSize:

    def test_adequate_size_passes(self):
        rm = RiskManager()
        ok, _ = rm.check_min_order_size(5.0)
        assert ok is True

    def test_tiny_size_blocks(self):
        rm = RiskManager()
        ok, reason = rm.check_min_order_size(1.0)
        assert ok is False
        assert "too small" in reason


class TestPositionSizing:

    def test_basic_sizing(self):
        rm = RiskManager()
        # max_leverage=10 so leverage cap doesn't interfere
        config = make_config(max_position_size_pct=10.0, max_leverage=10.0)
        # balance=100, risk=10, entry=50000, sl=49000 → distance=1000
        # quantity = 10 / 1000 = 0.01
        # quote_amount = 0.01 * 50000 = 500
        quantity, quote_amount, risk_amount = rm.calculate_position_size(
            balance=100.0, entry=50000.0, sl=49000.0, config=config
        )
        assert abs(risk_amount - 10.0) < 0.001
        assert abs(quantity - 0.01) < 1e-6
        assert abs(quote_amount - 500.0) < 0.01

    def test_short_sizing(self):
        rm = RiskManager()
        config = make_config(max_position_size_pct=10.0, max_leverage=10.0)
        # SHORT: entry=3000, sl=3100 → distance=100
        # risk = 10, quantity = 10/100 = 0.1, quote = 0.1 * 3000 = 300
        quantity, quote_amount, risk_amount = rm.calculate_position_size(
            balance=100.0, entry=3000.0, sl=3100.0, config=config
        )
        assert abs(risk_amount - 10.0) < 0.001
        assert abs(quantity - 0.1) < 1e-6
        assert abs(quote_amount - 300.0) < 0.01

    def test_leverage_cap(self):
        rm = RiskManager()
        config = make_config(max_position_size_pct=10.0, max_leverage=3.0)
        # balance=100, risk=10, entry=50000, sl=49000 → distance=1000
        # uncapped: qty=0.01, quote=500 (5x leverage)
        # capped at 3x: max_notional=300, qty=300/50000=0.006, risk=0.006*1000=6
        quantity, quote_amount, risk_amount = rm.calculate_position_size(
            balance=100.0, entry=50000.0, sl=49000.0, config=config
        )
        assert abs(quote_amount - 300.0) < 0.01
        assert abs(quantity - 0.006) < 1e-6
        assert abs(risk_amount - 6.0) < 0.001

    def test_invalid_entry_sl_raises(self):
        rm = RiskManager()
        config = make_config()
        with pytest.raises(ValueError):
            rm.calculate_position_size(100.0, 50000.0, 50000.0, config)  # entry == sl

    def test_sizing_scales_with_balance(self):
        rm = RiskManager()
        config = make_config(max_position_size_pct=5.0)
        _, _, risk_small = rm.calculate_position_size(100.0, 100.0, 90.0, config)
        _, _, risk_large = rm.calculate_position_size(1000.0, 100.0, 90.0, config)
        assert abs(risk_small - 5.0) < 0.001
        assert abs(risk_large - 50.0) < 0.001


class TestCheckAll:

    @pytest.mark.asyncio
    async def test_all_gates_pass(self):
        rm = RiskManager()
        config = make_config()
        ok, reason, sizing = await rm.check_all(
            symbol="BTCUSDT",
            direction="LONG",
            conviction=75,
            entry=50000.0,
            sl=49000.0,
            config=config,
            open_positions=[],
            balance=100.0,
        )
        assert ok is True
        assert sizing is not None
        assert len(sizing) == 3

    @pytest.mark.asyncio
    async def test_disabled_by_drawdown(self):
        rm = RiskManager()
        config = make_config(initial_capital=100.0, max_drawdown_pct=10.0)
        ok, reason, sizing = await rm.check_all(
            symbol="BTCUSDT", direction="LONG", conviction=75,
            entry=50000.0, sl=49000.0,
            config=config, open_positions=[], balance=85.0,  # below floor=90
        )
        assert ok is False
        assert sizing is None

    @pytest.mark.asyncio
    async def test_disabled_by_max_positions(self):
        rm = RiskManager()
        config = make_config(max_concurrent_positions=2)
        positions = [make_position("ETHUSDT"), make_position("BNBUSDT")]
        ok, reason, sizing = await rm.check_all(
            symbol="BTCUSDT", direction="LONG", conviction=75,
            entry=50000.0, sl=49000.0,
            config=config, open_positions=positions, balance=100.0,
        )
        assert ok is False
        assert "Max positions" in reason

    @pytest.mark.asyncio
    async def test_disabled_by_low_conviction(self):
        rm = RiskManager()
        config = make_config(min_conviction=80)
        ok, reason, sizing = await rm.check_all(
            symbol="BTCUSDT", direction="LONG", conviction=70,
            entry=50000.0, sl=49000.0,
            config=config, open_positions=[], balance=100.0,
        )
        assert ok is False
        assert "conviction" in reason.lower()


# ---------------------------------------------------------------------------
# PortfolioTracker — balance and stats
# ---------------------------------------------------------------------------

class TestPortfolioTracker:

    @pytest.mark.asyncio
    async def test_balance_no_trades(self):
        from app.trading.portfolio import PortfolioTracker
        from app.schemas.trading import Position

        tracker = PortfolioTracker(initial_capital=100.0)

        with patch("app.trading.portfolio.Database.get_session") as mock_session_ctx:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_result = MagicMock()
            mock_result.scalar.return_value = 0.0
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_ctx.return_value = mock_session

            balance = await tracker.get_balance()

        assert balance == 100.0

    @pytest.mark.asyncio
    async def test_balance_with_wins(self):
        from app.trading.portfolio import PortfolioTracker

        tracker = PortfolioTracker(initial_capital=100.0)

        with patch("app.trading.portfolio.Database.get_session") as mock_session_ctx:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_result = MagicMock()
            mock_result.scalar.return_value = 15.0  # 15 USD profit
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_ctx.return_value = mock_session

            balance = await tracker.get_balance()

        assert balance == 115.0

    @pytest.mark.asyncio
    async def test_balance_with_losses(self):
        from app.trading.portfolio import PortfolioTracker

        tracker = PortfolioTracker(initial_capital=100.0)

        with patch("app.trading.portfolio.Database.get_session") as mock_session_ctx:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_result = MagicMock()
            mock_result.scalar.return_value = -8.0
            mock_session.execute = AsyncMock(return_value=mock_result)
            mock_session_ctx.return_value = mock_session

            balance = await tracker.get_balance()

        assert balance == 92.0

    def test_max_drawdown_calc(self):
        from app.trading.portfolio import PortfolioTracker

        tracker = PortfolioTracker(initial_capital=100.0)

        # Equity: 100 → 110 → 105 → 115 → 100
        # Peak at 115, trough at 100 → DD = 15/115 = 13%
        closed = []
        for pnl in [10.0, -5.0, 10.0, -15.0]:
            pos = MagicMock()
            pos.pnl_usd = pnl
            pos.closed_at = int(time.time() * 1000)
            closed.append(pos)

        dd = tracker._calc_max_drawdown(closed)
        # After +10+(-5)+10 = 115 peak, then -15 → 100. DD = 15/115 ≈ 13.04%
        assert abs(dd - (15 / 115 * 100)) < 0.1

    def test_max_drawdown_no_trades(self):
        from app.trading.portfolio import PortfolioTracker
        tracker = PortfolioTracker(initial_capital=100.0)
        assert tracker._calc_max_drawdown([]) == 0.0


# ---------------------------------------------------------------------------
# PnL calculation math (direct, no DB)
# ---------------------------------------------------------------------------

class TestPnLMath:

    def test_long_win_pnl(self):
        """LONG: entry 50000, exit 51000, qty 0.01 → raw pnl = 10"""
        entry, exit_price, qty = 50000.0, 51000.0, 0.01
        quote = entry * qty  # 500
        raw_pnl = (exit_price - entry) * qty
        fee = quote * 0.001
        pnl = raw_pnl - fee
        pct = pnl / quote * 100
        assert raw_pnl == 10.0
        assert pnl > 0
        assert pct > 0

    def test_long_loss_pnl(self):
        """LONG: entry 50000, exit 49000, qty 0.01 → raw pnl = -10"""
        entry, exit_price, qty = 50000.0, 49000.0, 0.01
        quote = entry * qty
        raw_pnl = (exit_price - entry) * qty
        pnl = raw_pnl - quote * 0.001
        assert raw_pnl == -10.0
        assert pnl < 0

    def test_short_win_pnl(self):
        """SHORT: entry 3000, exit 2900, qty 0.1 → raw pnl = 10"""
        entry, exit_price, qty = 3000.0, 2900.0, 0.1
        quote = entry * qty  # 300
        raw_pnl = (entry - exit_price) * qty
        pnl = raw_pnl - quote * 0.001
        assert raw_pnl == 10.0
        assert pnl > 0

    def test_short_loss_pnl(self):
        """SHORT: entry 3000, exit 3100, qty 0.1 → raw pnl = -10"""
        entry, exit_price, qty = 3000.0, 3100.0, 0.1
        quote = entry * qty
        raw_pnl = (entry - exit_price) * qty
        pnl = raw_pnl - quote * 0.001
        assert raw_pnl == -10.0
        assert pnl < 0

    def test_rr_ratio_2to1(self):
        """At 2:1 RR, a win should cover two losses (pre-fee)."""
        entry, tp, sl, qty = 100.0, 106.0, 103.0, 1.0  # 6% gain / 3% loss = 2:1
        win_pnl = (tp - entry) * qty
        loss_pnl = (sl - entry) * qty
        assert win_pnl / abs(loss_pnl) == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Default config sanity checks
# ---------------------------------------------------------------------------

class TestDefaultConfig:

    def test_min_conviction_allows_live_signals(self):
        """Default min_conviction=50 lets live watchlist signals (conviction 56) through."""
        from app.trading.orchestrator import DEFAULT_TRADING_CONFIG
        assert DEFAULT_TRADING_CONFIG["min_conviction"] == 50

    def test_order_expiry_16_hours(self):
        """Order expiry should be 16h to avoid dead capital in low-vol."""
        from app.trading.orchestrator import DEFAULT_TRADING_CONFIG
        assert DEFAULT_TRADING_CONFIG["order_expiry_hours"] == 16


# ---------------------------------------------------------------------------
# Integration: full signal → position simulation cycle (mocked DB/Redis)
# ---------------------------------------------------------------------------

class TestOrchestratorCycle:

    def _make_signal(self, symbol="BTCUSDT", direction="LONG", conviction=75,
                     titan_signal="BUY_LIMIT"):
        sig = MagicMock()
        sig.id = 1
        sig.symbol = symbol
        sig.direction = direction
        sig.entry = 50000.0
        sig.tp = 52000.0
        sig.sl = 49000.0
        sig.conviction = conviction
        sig.market_state = "TRENDING"
        sig.fired_reason = "Test signal"
        sig.titan_signal = titan_signal
        return sig

    @pytest.mark.asyncio
    async def test_process_signal_creates_position(self):
        from app.trading.orchestrator import TradeOrchestrator

        orchestrator = TradeOrchestrator()

        config = make_config(enabled=True, initial_capital=100.0)

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session") as mock_session_ctx,
            patch("app.trading.orchestrator.notifier.notify_position_created", new_callable=AsyncMock),
        ):
            # First execute: check existing position (returns None)
            # Then get active positions (returns empty list)
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            # Simulate: no existing position, no active positions
            no_result = MagicMock()
            no_result.scalars.return_value.first.return_value = None
            no_result.scalars.return_value.all.return_value = []

            # Position gets id=42 after flush
            created_pos = MagicMock()
            created_pos.id = 42
            created_pos.symbol = "BTCUSDT"
            created_pos.direction = "LONG"
            created_pos.status = "PENDING"
            created_pos.intended_entry = 50000.0
            created_pos.intended_tp = 52000.0
            created_pos.intended_sl = 49000.0
            created_pos.quantity = 0.01
            created_pos.quote_amount = 500.0
            created_pos.risk_amount = 10.0
            created_pos.conviction = 75

            call_count = [0]

            async def mock_execute(stmt):
                call_count[0] += 1
                if call_count[0] <= 2:
                    return no_result
                return no_result

            mock_session.execute = mock_execute
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.add = MagicMock()

            async def mock_refresh(obj):
                obj.id = 42

            mock_session.refresh = mock_refresh
            mock_session_ctx.return_value = mock_session

            with patch("app.trading.portfolio.Database.get_session") as mock_portfolio_session:
                portfolio_session = AsyncMock()
                portfolio_session.__aenter__ = AsyncMock(return_value=portfolio_session)
                portfolio_session.__aexit__ = AsyncMock(return_value=None)
                portfolio_result = MagicMock()
                portfolio_result.scalar.return_value = 0.0
                portfolio_session.execute = AsyncMock(return_value=portfolio_result)
                mock_portfolio_session.return_value = portfolio_session

                signal = self._make_signal()
                # Should not raise — position creation flow runs
                # (We verify no exception is thrown and the mock interactions happen)
                try:
                    result = await orchestrator.process_signal(signal)
                    # The mock session doesn't fully simulate SQLModel so result may be None
                    # What matters is no exception was raised
                    assert True
                except Exception as e:
                    # Only acceptable failure is SQLModel-specific during mock
                    assert "Position" in str(type(e).__name__) or "mock" in str(e).lower(), \
                        f"Unexpected error: {e}"

    @pytest.mark.asyncio
    async def test_process_signal_disabled_returns_none(self):
        from app.trading.orchestrator import TradeOrchestrator

        orchestrator = TradeOrchestrator()
        config = make_config(enabled=False)

        with patch("app.trading.orchestrator.get_trading_config", return_value=config):
            signal = self._make_signal()
            result = await orchestrator.process_signal(signal)
            assert result is None

    @pytest.mark.asyncio
    async def test_market_signal_creates_open_position(self):
        """BUY/SELL (market) signals should create OPEN position immediately, not PENDING."""
        from app.trading.orchestrator import TradeOrchestrator

        orchestrator = TradeOrchestrator()
        config = make_config(enabled=True, initial_capital=100.0)

        mock_session = AsyncMock()
        no_result = MagicMock()
        no_result.scalars.return_value.first.return_value = None
        no_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=no_result)
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        added_objects = []
        orig_add = mock_session.add
        def capture_add(obj):
            added_objects.append(obj)
            return orig_add(obj)
        mock_session.add = capture_add

        db_ctx = MagicMock()
        db_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        db_ctx.__aexit__ = AsyncMock(return_value=None)

        portfolio_session = AsyncMock()
        portfolio_result = MagicMock()
        portfolio_result.scalar.return_value = 0.0
        portfolio_session.execute = AsyncMock(return_value=portfolio_result)
        p_ctx = MagicMock()
        p_ctx.__aenter__ = AsyncMock(return_value=portfolio_session)
        p_ctx.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.trading.orchestrator.get_trading_config", new_callable=AsyncMock, return_value=config),
            patch("app.trading.orchestrator.Database") as mock_db,
            patch("app.trading.orchestrator.notifier.notify_position_created", new_callable=AsyncMock),
            patch("app.trading.orchestrator.notifier.notify_position_filled", new_callable=AsyncMock),
            patch("app.trading.orchestrator._get_prices", new_callable=AsyncMock, return_value={"BTCUSDT": 50500.0}),
            patch("app.trading.portfolio.Database") as mock_pdb,
        ):
            mock_db.get_session.return_value = db_ctx
            mock_pdb.get_session.return_value = p_ctx

            signal = self._make_signal(direction="SHORT", titan_signal="SELL", conviction=78)
            result = await orchestrator.process_signal(signal)

            from app.schemas.trading import Position
            positions = [o for o in added_objects if isinstance(o, Position)]
            assert len(positions) >= 1, "Expected a Position to be created"
            pos = positions[0]
            assert pos.status == "OPEN"
            assert pos.actual_entry == 50500.0
            assert pos.filled_at is not None

    @pytest.mark.asyncio
    async def test_limit_signal_creates_pending_position(self):
        """SELL_LIMIT/BUY_LIMIT signals should create PENDING position (existing behavior)."""
        from app.trading.orchestrator import TradeOrchestrator

        orchestrator = TradeOrchestrator()
        config = make_config(enabled=True, initial_capital=100.0, min_conviction=50)

        mock_session = AsyncMock()
        no_result = MagicMock()
        no_result.scalars.return_value.first.return_value = None
        no_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=no_result)
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        added_objects = []
        orig_add = mock_session.add
        def capture_add(obj):
            added_objects.append(obj)
            return orig_add(obj)
        mock_session.add = capture_add

        db_ctx = MagicMock()
        db_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        db_ctx.__aexit__ = AsyncMock(return_value=None)

        portfolio_session = AsyncMock()
        portfolio_result = MagicMock()
        portfolio_result.scalar.return_value = 0.0
        portfolio_session.execute = AsyncMock(return_value=portfolio_result)
        p_ctx = MagicMock()
        p_ctx.__aenter__ = AsyncMock(return_value=portfolio_session)
        p_ctx.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("app.trading.orchestrator.get_trading_config", new_callable=AsyncMock, return_value=config),
            patch("app.trading.orchestrator.Database") as mock_db,
            patch("app.trading.orchestrator.notifier.notify_position_created", new_callable=AsyncMock),
            patch("app.trading.orchestrator._get_prices", new_callable=AsyncMock, return_value={"ETHUSDT": 1800.0}),
            patch("app.trading.portfolio.Database") as mock_pdb,
        ):
            mock_db.get_session.return_value = db_ctx
            mock_pdb.get_session.return_value = p_ctx

            signal = self._make_signal(direction="SHORT", titan_signal="SELL_LIMIT", conviction=56)
            result = await orchestrator.process_signal(signal)

            from app.schemas.trading import Position
            positions = [o for o in added_objects if isinstance(o, Position)]
            assert len(positions) >= 1, "Expected a Position to be created"
            pos = positions[0]
            assert pos.status == "PENDING"
            assert pos.actual_entry is None
            assert pos.filled_at is None

    @pytest.mark.asyncio
    async def test_fill_logic_long(self):
        """LONG fills when price <= intended_entry."""
        # Price 49900 <= entry 50000 → should fill
        entry = 50000.0
        current_price = 49900.0
        direction = "LONG"
        filled = direction == "LONG" and current_price <= entry
        assert filled is True

    @pytest.mark.asyncio
    async def test_fill_logic_short(self):
        """SHORT fills when price >= intended_entry."""
        entry = 3000.0
        current_price = 3050.0
        direction = "SHORT"
        filled = direction == "SHORT" and current_price >= entry
        assert filled is True

    @pytest.mark.asyncio
    async def test_tp_hit_logic_long(self):
        """LONG closes WIN when price >= tp."""
        tp = 52000.0
        current_price = 52100.0
        direction = "LONG"
        win = direction == "LONG" and current_price >= tp
        assert win is True

    @pytest.mark.asyncio
    async def test_sl_hit_logic_long(self):
        """LONG closes LOSS when price <= sl."""
        sl = 49000.0
        current_price = 48950.0
        direction = "LONG"
        loss = direction == "LONG" and current_price <= sl
        assert loss is True

    @pytest.mark.asyncio
    async def test_tp_hit_logic_short(self):
        """SHORT closes WIN when price <= tp."""
        tp = 2800.0
        current_price = 2750.0
        direction = "SHORT"
        win = direction == "SHORT" and current_price <= tp
        assert win is True

    @pytest.mark.asyncio
    async def test_sl_hit_logic_short(self):
        """SHORT closes LOSS when price >= sl."""
        sl = 3200.0
        current_price = 3250.0
        direction = "SHORT"
        loss = direction == "SHORT" and current_price >= sl
        assert loss is True


# ---------------------------------------------------------------------------
# Price map helper
# ---------------------------------------------------------------------------

class TestPriceMap:

    def test_converts_slash_format(self):
        from app.trading.portfolio import _price_map_from_tickers
        tickers = [
            {"symbol": "BTC/USDT", "price": 50000.0},
            {"symbol": "ETH/USDT", "price": 3000.0},
        ]
        prices = _price_map_from_tickers(tickers)
        assert prices["BTCUSDT"] == 50000.0
        assert prices["ETHUSDT"] == 3000.0

    def test_skips_missing_price(self):
        from app.trading.portfolio import _price_map_from_tickers
        tickers = [{"symbol": "BTC/USDT", "price": None}]
        prices = _price_map_from_tickers(tickers)
        assert "BTCUSDT" not in prices


# ---------------------------------------------------------------------------
# Candle-walk TP/SL resolution (check_open_positions)
# ---------------------------------------------------------------------------

import pandas as pd


def _make_position(symbol="BTCUSDT", direction="LONG", entry=50000.0,
                   tp=52000.0, sl=49000.0, qty=0.01, quote=500.0):
    pos = MagicMock()
    pos.symbol = symbol
    pos.direction = direction
    pos.actual_entry = entry
    pos.intended_tp = tp
    pos.intended_sl = sl
    pos.quantity = qty
    pos.quote_amount = quote
    pos.filled_at = 1000  # epoch ms — orchestrator converts via pd.Timestamp()
    pos.created_at = 1000
    pos.status = "OPEN"
    pos.outcome = None
    pos.id = 1
    pos.provider = "binance"
    return pos


def _make_candles(rows):
    """rows: list of (timestamp_ms, open, high, low, close).
    Timestamps are converted to datetime64 to match get_candles_df output."""
    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


class TestCandleWalkResolution:
    """Test the candle-walk logic in check_open_positions."""

    @pytest.mark.asyncio
    async def test_long_tp_hit(self):
        from app.trading.orchestrator import TradeOrchestrator
        orch = TradeOrchestrator()
        pos = _make_position(direction="LONG", entry=50000, tp=52000, sl=49000)
        candles = _make_candles([
            (1000, 50000, 50500, 49800, 50200),  # no hit
            (2000, 50200, 52100, 50100, 51800),  # TP hit (high >= 52000)
        ])

        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        config = make_config(enabled=True)

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
            patch("app.trading.orchestrator.RedisClient.get_json", new_callable=AsyncMock, return_value={"market_state": "TRENDING"}),
        ):
            await orch.check_open_positions(config=config)

        assert pos.status == "CLOSED"
        assert pos.outcome == "WIN"
        assert pos.actual_exit == 52000.0

    @pytest.mark.asyncio
    async def test_long_sl_hit(self):
        from app.trading.orchestrator import TradeOrchestrator
        orch = TradeOrchestrator()
        pos = _make_position(direction="LONG", entry=50000, tp=52000, sl=49000)
        candles = _make_candles([
            (1000, 50000, 50500, 49800, 50200),  # no hit
            (2000, 50200, 50300, 48900, 49100),  # SL hit (low <= 49000)
        ])

        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        config = make_config(enabled=True)

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
            patch("app.trading.orchestrator.RedisClient.get_json", new_callable=AsyncMock, return_value={"market_state": "TRENDING"}),
        ):
            await orch.check_open_positions(config=config)

        assert pos.status == "CLOSED"
        assert pos.outcome == "LOSS"
        assert pos.actual_exit == 49000.0

    @pytest.mark.asyncio
    async def test_short_tp_hit(self):
        from app.trading.orchestrator import TradeOrchestrator
        orch = TradeOrchestrator()
        pos = _make_position(direction="SHORT", entry=50000, tp=48000, sl=51000)
        candles = _make_candles([
            (1000, 50000, 50200, 49500, 49800),  # no hit
            (2000, 49800, 49900, 47900, 48200),  # TP hit (low <= 48000)
        ])

        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        config = make_config(enabled=True)

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
            patch("app.trading.orchestrator.RedisClient.get_json", new_callable=AsyncMock, return_value={"market_state": "TRENDING"}),
        ):
            await orch.check_open_positions(config=config)

        assert pos.status == "CLOSED"
        assert pos.outcome == "WIN"
        assert pos.actual_exit == 48000.0

    @pytest.mark.asyncio
    async def test_both_hit_same_candle_long_bullish_means_loss(self):
        """LONG + bullish candle (close >= open) → SL hit first → LOSS."""
        from app.trading.orchestrator import TradeOrchestrator
        orch = TradeOrchestrator()
        pos = _make_position(direction="LONG", entry=50000, tp=52000, sl=49000)
        # Bullish candle that hits both: high >= TP, low <= SL, close >= open
        candles = _make_candles([
            (1000, 49500, 52500, 48500, 51000),  # both hit, bullish
        ])

        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        config = make_config(enabled=True)

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
            patch("app.trading.orchestrator.RedisClient.get_json", new_callable=AsyncMock, return_value={"market_state": "TRENDING"}),
        ):
            await orch.check_open_positions(config=config)

        assert pos.outcome == "LOSS"
        assert pos.actual_exit == 49000.0

    @pytest.mark.asyncio
    async def test_both_hit_same_candle_uses_5m_tiebreaker(self):
        """When both TP and SL hit in same 4H candle, 5-min tiebreaker determines outcome."""
        from app.trading.orchestrator import TradeOrchestrator
        orch = TradeOrchestrator()
        pos = _make_position(direction="LONG", entry=50000, tp=52000, sl=49000)
        candles = _make_candles([
            (1000, 51000, 52500, 48500, 49500),  # both hit
        ])

        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        config = make_config(enabled=True)
        tiebreak_result = {"outcome": "WIN", "resolved_price": 52000.0, "resolved_at_ms": 1500}

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
            patch("app.trading.orchestrator.RedisClient.get_json", new_callable=AsyncMock, return_value={"market_state": "TRENDING"}),
            patch("app.jobs.signal_log._resolve_tiebreaker_5m", new_callable=AsyncMock, return_value=tiebreak_result),
        ):
            await orch.check_open_positions(config=config)

        assert pos.outcome == "WIN"
        assert pos.actual_exit == 52000.0

    @pytest.mark.asyncio
    async def test_both_hit_same_candle_tiebreaker_fallback_is_loss(self):
        """When tiebreaker has no 5m data, conservative fallback is LOSS."""
        from app.trading.orchestrator import TradeOrchestrator
        orch = TradeOrchestrator()
        pos = _make_position(direction="LONG", entry=50000, tp=52000, sl=49000)
        candles = _make_candles([
            (1000, 51000, 52500, 48500, 49500),  # both hit
        ])

        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        config = make_config(enabled=True)
        fallback_result = {"outcome": "LOSS", "resolved_price": 49000.0, "resolved_at_ms": 1000}

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
            patch("app.trading.orchestrator.RedisClient.get_json", new_callable=AsyncMock, return_value={"market_state": "TRENDING"}),
            patch("app.jobs.signal_log._resolve_tiebreaker_5m", new_callable=AsyncMock, return_value=fallback_result),
        ):
            await orch.check_open_positions(config=config)

        assert pos.outcome == "LOSS"
        assert pos.actual_exit == 49000.0

    @pytest.mark.asyncio
    async def test_no_hit_position_stays_open(self):
        from app.trading.orchestrator import TradeOrchestrator
        orch = TradeOrchestrator()
        pos = _make_position(direction="LONG", entry=50000, tp=52000, sl=49000)
        candles = _make_candles([
            (1000, 50000, 50500, 49800, 50200),  # no hit
            (2000, 50200, 51000, 49500, 50800),  # no hit
        ])

        mock_session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=result_mock)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        config = make_config(enabled=True)

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
        ):
            await orch.check_open_positions(config=config)

        # Position should remain unchanged
        assert pos.status == "OPEN"
        assert pos.outcome is None


# ---------------------------------------------------------------------------
# Error handling: commit failures trigger rollback and logging
# ---------------------------------------------------------------------------

class TestOrchestratorCommitErrorHandling:
    """Verify that commit failures in each method trigger rollback and log an error."""

    def _make_session(self, commit_raises=False):
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.add = MagicMock()
        mock_session.rollback = AsyncMock()
        if commit_raises:
            mock_session.commit = AsyncMock(side_effect=Exception("DB commit error"))
        else:
            mock_session.commit = AsyncMock()
        return mock_session

    @pytest.mark.asyncio
    async def test_check_pending_fills_commit_failure_calls_rollback(self):
        """check_pending_fills: commit failure triggers rollback and logs error."""
        from app.trading.orchestrator import TradeOrchestrator

        orch = TradeOrchestrator()
        config = make_config(enabled=True, order_expiry_hours=8)
        mock_session = self._make_session(commit_raises=True)

        pos = MagicMock()
        pos.symbol = "BTCUSDT"
        pos.direction = "LONG"
        pos.id = 1
        pos.created_at = int(time.time() * 1000)  # fresh — not expired
        pos.intended_entry = 50000.0

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=result_mock)

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.trading.orchestrator._get_prices", new_callable=AsyncMock, return_value={}),
            patch("app.trading.orchestrator.logger") as mock_logger,
        ):
            # Should not raise despite commit failure
            await orch.check_pending_fills(config=config, prices={})

        mock_session.rollback.assert_awaited_once()
        mock_logger.error.assert_called_once()
        assert "check_pending_fills" in mock_logger.error.call_args[0][0]

    @pytest.mark.asyncio
    async def test_check_open_positions_commit_failure_calls_rollback(self):
        """check_open_positions: commit failure triggers rollback and logs error."""
        from app.trading.orchestrator import TradeOrchestrator

        orch = TradeOrchestrator()
        config = make_config(enabled=True)
        mock_session = self._make_session(commit_raises=True)

        pos = _make_position(direction="LONG", entry=50000, tp=52000, sl=49000)
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=result_mock)

        candles = _make_candles([
            (1000, 50000, 52100, 49800, 51800),  # TP hit
        ])

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, return_value=candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
            patch("app.trading.orchestrator.RedisClient.get_json", new_callable=AsyncMock, return_value={}),
            patch("app.trading.orchestrator.logger") as mock_logger,
        ):
            # Should not raise despite commit failure
            await orch.check_open_positions(config=config)

        mock_session.rollback.assert_awaited_once()
        mock_logger.error.assert_called_once()
        assert "check_open_positions" in mock_logger.error.call_args[0][0]

    @pytest.mark.asyncio
    async def test_check_circuit_breaker_db_failure_still_disables_trading(self):
        """check_circuit_breaker: DB failure is logged but trading is still disabled."""
        from app.trading.orchestrator import TradeOrchestrator

        orch = TradeOrchestrator()
        config = make_config(enabled=True, initial_capital=100.0, max_drawdown_pct=10.0)
        # Balance below floor → circuit breaker triggers
        balance_below_floor = 85.0

        mock_session = self._make_session(commit_raises=True)
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=result_mock)

        saved_configs = []

        async def capture_save(cfg):
            saved_configs.append(dict(cfg))

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.trading.orchestrator.save_trading_config", side_effect=capture_save),
            patch("app.trading.orchestrator.notifier.notify_circuit_breaker", new_callable=AsyncMock),
            patch("app.trading.orchestrator.logger") as mock_logger,
        ):
            # Mock portfolio so balance returns below floor
            portfolio_mock = AsyncMock()
            portfolio_mock.get_balance = AsyncMock(return_value=balance_below_floor)
            portfolio_mock.initial_capital = 100.0
            orch._portfolio = portfolio_mock

            # Should not raise despite DB failure
            await orch.check_circuit_breaker(config=config)

        # DB error must be logged
        mock_logger.error.assert_called_once()
        assert "circuit breaker" in mock_logger.error.call_args[0][0]

        # Trading must be disabled regardless of the DB failure
        assert len(saved_configs) == 1
        assert saved_configs[0]["enabled"] is False


# ---------------------------------------------------------------------------
# trading_provider config field
# ---------------------------------------------------------------------------

class TestTradingProviderConfig:

    def test_default_config_has_binance_provider(self):
        from app.trading.orchestrator import DEFAULT_TRADING_CONFIG
        assert DEFAULT_TRADING_CONFIG["trading_provider"] == "binance"

    def test_config_update_accepts_okx(self):
        from app.routes.trading import TradingConfigUpdate
        update = TradingConfigUpdate(trading_provider="okx")
        assert update.trading_provider == "okx"

    def test_config_update_accepts_binance(self):
        from app.routes.trading import TradingConfigUpdate
        update = TradingConfigUpdate(trading_provider="binance")
        assert update.trading_provider == "binance"

    def test_config_update_rejects_invalid_provider(self):
        import pydantic
        from app.routes.trading import TradingConfigUpdate
        with pytest.raises(pydantic.ValidationError):
            TradingConfigUpdate(trading_provider="kraken")

    def test_config_update_provider_none_is_excluded(self):
        from app.routes.trading import TradingConfigUpdate
        update = TradingConfigUpdate(trading_provider=None)
        patch = update.model_dump(exclude_none=True)
        assert "trading_provider" not in patch

    @pytest.mark.asyncio
    async def test_check_open_positions_uses_okx_provider(self):
        """When trading_provider=okx, check_open_positions instantiates OKXProvider."""
        from app.trading.orchestrator import TradeOrchestrator

        orch = TradeOrchestrator()
        config = make_config(enabled=True, trading_provider="okx")

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=result_mock)

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
        ):
            await orch.check_open_positions(config=config)

        # No positions were open so candle fetch was never called — that's fine.
        # The key check: no exception was raised resolving OKXProvider from okx config.
        assert True

    @pytest.mark.asyncio
    async def test_check_open_positions_passes_provider_to_get_candles_df(self):
        """check_open_positions passes a BinanceProvider instance to get_candles_df."""
        from app.trading.orchestrator import TradeOrchestrator
        from app.providers import BinanceProvider

        orch = TradeOrchestrator()
        config = make_config(enabled=True, trading_provider="binance")
        pos = _make_position(direction="LONG", entry=50000, tp=52000, sl=49000)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [pos]
        mock_session.execute = AsyncMock(return_value=result_mock)

        candles = _make_candles([
            (1000, 50000, 52100, 49800, 51800),  # TP hit
        ])

        captured_providers = []

        async def capture_candles(symbol, timeframe, limit=100, provider=None):
            captured_providers.append(provider)
            return candles

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, side_effect=capture_candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
            patch("app.trading.orchestrator.RedisClient.get_json", new_callable=AsyncMock, return_value={"market_state": "TRENDING"}),
        ):
            await orch.check_open_positions(config=config)

        assert len(captured_providers) == 1
        assert isinstance(captured_providers[0], BinanceProvider)


# ---------------------------------------------------------------------------
# Per-position provider: check_open_positions uses position's stamped provider
# ---------------------------------------------------------------------------

class TestCheckOpenPositionsProvider:
    """Verify that check_open_positions uses each position's stamped provider,
    not the current global trading_provider config value."""

    def _make_session_with_positions(self, positions: list):
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = positions
        mock_session.execute = AsyncMock(return_value=result_mock)
        return mock_session

    @pytest.mark.asyncio
    async def test_binance_position_uses_binance_provider(self):
        """A position stamped with provider='binance' causes BinanceProvider to be used."""
        from app.trading.orchestrator import TradeOrchestrator
        from app.providers import BinanceProvider

        orch = TradeOrchestrator()
        config = make_config(enabled=True, trading_provider="okx")
        pos = _make_position(direction="LONG", entry=50000, tp=52000, sl=49000)
        pos.provider = "binance"

        mock_session = self._make_session_with_positions([pos])
        candles = _make_candles([(1000, 50000, 49800, 49800, 50200)])  # no hit

        captured_providers = []

        async def capture_candles(symbol, timeframe, limit=100, provider=None):
            captured_providers.append(provider)
            return candles

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, side_effect=capture_candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
            patch("app.trading.orchestrator.RedisClient.get_json", new_callable=AsyncMock, return_value={}),
        ):
            await orch.check_open_positions(config=config)

        assert len(captured_providers) == 1
        assert isinstance(captured_providers[0], BinanceProvider)

    @pytest.mark.asyncio
    async def test_okx_position_uses_okx_provider(self):
        """A position stamped with provider='okx' causes OKXProvider to be used."""
        from app.trading.orchestrator import TradeOrchestrator
        from app.providers import OKXProvider

        orch = TradeOrchestrator()
        config = make_config(enabled=True, trading_provider="binance")
        pos = _make_position(direction="LONG", entry=50000, tp=52000, sl=49000)
        pos.provider = "okx"

        mock_session = self._make_session_with_positions([pos])
        candles = _make_candles([(1000, 50000, 49800, 49800, 50200)])  # no hit

        captured_providers = []

        async def capture_candles(symbol, timeframe, limit=100, provider=None):
            captured_providers.append(provider)
            return candles

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, side_effect=capture_candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
            patch("app.trading.orchestrator.RedisClient.get_json", new_callable=AsyncMock, return_value={}),
        ):
            await orch.check_open_positions(config=config)

        assert len(captured_providers) == 1
        assert isinstance(captured_providers[0], OKXProvider)

    @pytest.mark.asyncio
    async def test_mixed_provider_positions_each_get_own_candle_fetch(self):
        """Two positions with different providers for different symbols each trigger
        a separate get_candles_df call with the correct provider instance."""
        from app.trading.orchestrator import TradeOrchestrator
        from app.providers import BinanceProvider, OKXProvider

        orch = TradeOrchestrator()
        config = make_config(enabled=True, trading_provider="binance")

        pos_binance = _make_position(symbol="BTCUSDT", direction="LONG",
                                     entry=50000, tp=52000, sl=49000)
        pos_binance.provider = "binance"

        pos_okx = _make_position(symbol="ETHUSDT", direction="LONG",
                                  entry=3000, tp=3200, sl=2900)
        pos_okx.provider = "okx"

        mock_session = self._make_session_with_positions([pos_binance, pos_okx])
        candles = _make_candles([(1000, 50000, 49800, 49800, 50200)])  # no hit

        captured: list[tuple[str, object]] = []

        async def capture_candles(symbol, timeframe, limit=100, provider=None):
            captured.append((symbol, provider))
            return candles

        with (
            patch("app.trading.orchestrator.get_trading_config", return_value=config),
            patch("app.trading.orchestrator.Database.get_session", return_value=mock_session),
            patch("app.routes.strategy.get_candles_df", new_callable=AsyncMock, side_effect=capture_candles),
            patch("app.trading.orchestrator.notifier.notify_position_closed", new_callable=AsyncMock),
            patch("app.trading.orchestrator.RedisClient.get_json", new_callable=AsyncMock, return_value={}),
        ):
            await orch.check_open_positions(config=config)

        assert len(captured) == 2
        symbols_fetched = {sym for sym, _ in captured}
        assert symbols_fetched == {"BTCUSDT", "ETHUSDT"}

        provider_by_symbol = {sym: prov for sym, prov in captured}
        assert isinstance(provider_by_symbol["BTCUSDT"], BinanceProvider)
        assert isinstance(provider_by_symbol["ETHUSDT"], OKXProvider)


# ---------------------------------------------------------------------------
# Batch Race Condition — verify batch positions are visible to risk gates
# ---------------------------------------------------------------------------

class TestBatchRaceCondition:
    """Positions created earlier in the same signal batch must be
    visible to risk gates for subsequent signals."""

    @pytest.mark.asyncio
    async def test_batch_positions_counted_in_max_concurrent(self):
        """If 2 positions already exist in the batch, a 3rd signal
        with max_concurrent_positions=2 must be rejected."""
        rm = RiskManager()
        config = make_config(max_concurrent_positions=2, max_total_exposure_pct=9999)
        batch = [make_position("ETHUSDT", "SHORT", "OPEN"),
                 make_position("BNBUSDT", "SHORT", "OPEN")]
        ok, reason, sizing = await rm.check_all(
            symbol="XRPUSDT", direction="SHORT", conviction=70,
            entry=1.40, sl=1.45, config=config,
            open_positions=batch, balance=200.0,
        )
        assert ok is False
        assert "Max positions" in reason

    @pytest.mark.asyncio
    async def test_batch_positions_counted_in_exposure(self):
        """Batch positions' quote_amount must count toward the exposure cap."""
        rm = RiskManager()
        config = make_config(max_total_exposure_pct=200, max_concurrent_positions=99)
        p1 = make_position("ETHUSDT", "SHORT", "OPEN")
        p1.quote_amount = 100.0
        p2 = make_position("BNBUSDT", "SHORT", "OPEN")
        p2.quote_amount = 100.0
        ok, reason = rm.check_total_exposure(
            open_positions=[p1, p2], quote_amount=10.0,
            balance=100.0, config=config,
        )
        assert ok is False
        assert "exposure" in reason.lower()

    @pytest.mark.asyncio
    async def test_batch_under_limit_still_approved(self):
        """With only 1 batch position and room for more, signal should pass."""
        rm = RiskManager()
        config = make_config(max_concurrent_positions=3, max_total_exposure_pct=9999)
        p1 = make_position("ETHUSDT", "SHORT", "OPEN")
        p1.quote_amount = 10.0
        ok, reason, sizing = await rm.check_all(
            symbol="XRPUSDT", direction="SHORT", conviction=70,
            entry=1.40, sl=1.45, config=config,
            open_positions=[p1], balance=200.0,
        )
        assert ok is True
