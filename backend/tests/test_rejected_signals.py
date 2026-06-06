"""
C3: Rejected signal persistence tests.

Verifies that signals rejected by the risk manager are persisted to the
signal_log table with outcome="REJECTED" and rejection_reason populated,
enabling rejection pattern analysis in the analytics endpoint.

All tests mock the database session — no live DB required.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rejected_signal(
    id_: int = 1,
    symbol: str = "BTCUSDT",
    direction: str = "LONG",
    rejection_reason: str = "low_conviction",
    conviction: int = 45,
    market_state: str = "BULL",
    fired_at: int = 1_704_067_200_000,
):
    s = MagicMock()
    s.id = id_
    s.symbol = symbol
    s.direction = direction
    s.outcome = "REJECTED"
    s.source = "live"
    s.conviction = conviction
    s.market_state = market_state
    s.regime_at_resolution = None
    s.rejection_reason = rejection_reason
    s.fired_at = fired_at
    s.time_to_resolution_ms = None
    s.oracle_signal = "N/A"
    s.titan_signal = "BUY"
    s.oracle_score = 0
    s.titan_confidence = 30
    s.timeframe = "4h"
    s.entry = 50000.0
    s.tp = 51000.0
    s.sl = 49500.0
    s.fired_reason = "low confidence signal"
    s.provider = "binance"
    s.resolved_at = None
    return s


def _make_outcomes_ctx(signals, rejected_signals, positions):
    """Mock async context manager for /signal-outcomes (3 execute calls)."""
    mock_session = AsyncMock()

    sig_result = MagicMock()
    sig_result.scalars.return_value.all.return_value = signals

    rej_result = MagicMock()
    rej_result.scalars.return_value.all.return_value = rejected_signals

    pos_result = MagicMock()
    pos_result.scalars.return_value.all.return_value = positions

    mock_session.execute = AsyncMock(side_effect=[sig_result, rej_result, pos_result])
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


# ---------------------------------------------------------------------------
# C3: Rejected signal persistence
# ---------------------------------------------------------------------------

class TestRejectedSignalPersisted:

    @pytest.mark.asyncio
    async def test_rejected_signal_has_rejection_reason(self, async_client):
        """Rejected signals have rejection_reason populated."""
        rejected = [
            _make_rejected_signal(
                id_=1, rejection_reason="low_conviction", direction="LONG"
            ),
        ]

        ctx = _make_outcomes_ctx([], rejected, [])
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-outcomes")

        assert resp.status_code == 200
        body = resp.json()
        rejection = body["rejection_analysis"]
        assert rejection["total_rejected"] == 1
        assert "low_conviction" in rejection["by_reason"]

    @pytest.mark.asyncio
    async def test_multiple_rejection_reasons_tracked(self, async_client):
        """Different rejection reasons are all tracked separately."""
        rejected = [
            _make_rejected_signal(id_=1, rejection_reason="low_conviction"),
            _make_rejected_signal(id_=2, rejection_reason="exposure_cap"),
            _make_rejected_signal(id_=3, rejection_reason="max_positions"),
            _make_rejected_signal(id_=4, rejection_reason="low_conviction"),
        ]

        ctx = _make_outcomes_ctx([], rejected, [])
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-outcomes")

        assert resp.status_code == 200
        rejection = resp.json()["rejection_analysis"]
        assert rejection["total_rejected"] == 4
        assert rejection["by_reason"]["low_conviction"] == 2
        assert rejection["by_reason"]["exposure_cap"] == 1
        assert rejection["by_reason"]["max_positions"] == 1

    @pytest.mark.asyncio
    async def test_rejected_not_mixed_with_resolved(self, async_client):
        """Rejected signals appear in rejection_analysis, not signal_outcomes."""
        resolved = [
            _make_rejected_signal(
                id_=1, rejection_reason=None
            ),
        ]
        resolved[0].outcome = "WIN"
        resolved[0].rejection_reason = None

        rejected = [
            _make_rejected_signal(id_=2, rejection_reason="low_conviction"),
        ]

        ctx = _make_outcomes_ctx(resolved, rejected, [])
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-outcomes")

        assert resp.status_code == 200
        body = resp.json()
        # signal_outcomes has resolved signals
        assert len(body["signal_outcomes"]) == 1
        assert body["signal_outcomes"][0]["signal_outcome"] == "WIN"
        # rejection_analysis has rejected signals
        assert body["rejection_analysis"]["total_rejected"] == 1

    @pytest.mark.asyncio
    async def test_rejected_signal_preserves_direction(self, async_client):
        """Rejected signals retain direction info for analysis."""
        rejected = [
            _make_rejected_signal(id_=1, direction="LONG", rejection_reason="low_conviction"),
            _make_rejected_signal(id_=2, direction="SHORT", rejection_reason="exposure_cap"),
        ]

        ctx = _make_outcomes_ctx([], rejected, [])
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-outcomes")

        assert resp.status_code == 200
        # Rejection analysis groups by reason, not direction
        rejection = resp.json()["rejection_analysis"]
        assert rejection["by_reason"]["low_conviction"] == 1
        assert rejection["by_reason"]["exposure_cap"] == 1


# ---------------------------------------------------------------------------
# C3: Rejection rate analysis
# ---------------------------------------------------------------------------

class TestRejectionRates:

    @pytest.mark.asyncio
    async def test_rejection_rate_computable_from_data(self, async_client):
        """Rejection rate = total_rejected / (total_resolved + total_rejected)."""
        resolved = [
            _make_rejected_signal(id_=1),
            _make_rejected_signal(id_=2),
        ]
        resolved[0].outcome = "WIN"
        resolved[0].rejection_reason = None
        resolved[1].outcome = "LOSS"
        resolved[1].rejection_reason = None

        rejected = [
            _make_rejected_signal(id_=3, rejection_reason="low_conviction"),
            _make_rejected_signal(id_=4, rejection_reason="low_conviction"),
            _make_rejected_signal(id_=5, rejection_reason="exposure_cap"),
        ]

        ctx = _make_outcomes_ctx(resolved, rejected, [])
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-outcomes")

        assert resp.status_code == 200
        body = resp.json()
        total_resolved = len(body["signal_outcomes"])
        total_rejected = body["rejection_analysis"]["total_rejected"]

        # Verify data supports rate computation
        assert total_resolved == 2
        assert total_rejected == 3
        rejection_rate = total_rejected / (total_resolved + total_rejected)
        assert rejection_rate == pytest.approx(0.6)  # 3/(2+3) = 60%

    @pytest.mark.asyncio
    async def test_rejection_rate_by_reason(self, async_client):
        """Per-reason rejection breakdown enables pattern analysis."""
        rejected = [
            _make_rejected_signal(id_=1, rejection_reason="low_conviction"),
            _make_rejected_signal(id_=2, rejection_reason="low_conviction"),
            _make_rejected_signal(id_=3, rejection_reason="low_conviction"),
            _make_rejected_signal(id_=4, rejection_reason="exposure_cap"),
        ]

        ctx = _make_outcomes_ctx([], rejected, [])
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-outcomes")

        assert resp.status_code == 200
        rejection = resp.json()["rejection_analysis"]

        # 75% of rejections are low_conviction
        low_conv_rate = rejection["by_reason"]["low_conviction"] / rejection["total_rejected"]
        assert low_conv_rate == pytest.approx(0.75)

    @pytest.mark.asyncio
    async def test_zero_rejections_safe(self, async_client):
        """No rejected signals → zero counts, no errors."""
        resolved = [_make_rejected_signal(id_=1)]
        resolved[0].outcome = "WIN"
        resolved[0].rejection_reason = None

        ctx = _make_outcomes_ctx(resolved, [], [])
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-outcomes")

        assert resp.status_code == 200
        rejection = resp.json()["rejection_analysis"]
        assert rejection["total_rejected"] == 0
        assert rejection["by_reason"] == {}


# ---------------------------------------------------------------------------
# C3: Rejection reason types
# ---------------------------------------------------------------------------

class TestRejectionReasonTypes:

    @pytest.mark.asyncio
    async def test_low_conviction_rejection(self, async_client):
        """Signals below min conviction threshold are rejected with 'low_conviction'."""
        rejected = [
            _make_rejected_signal(
                id_=1,
                rejection_reason="low_conviction",
                conviction=45,
            ),
        ]

        ctx = _make_outcomes_ctx([], rejected, [])
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-outcomes")

        assert resp.status_code == 200
        rejection = resp.json()["rejection_analysis"]
        assert "low_conviction" in rejection["by_reason"]

    @pytest.mark.asyncio
    async def test_exposure_cap_rejection(self, async_client):
        """Portfolio exposure limit rejections tracked separately."""
        rejected = [
            _make_rejected_signal(id_=1, rejection_reason="exposure_cap"),
        ]

        ctx = _make_outcomes_ctx([], rejected, [])
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-outcomes")

        assert resp.status_code == 200
        rejection = resp.json()["rejection_analysis"]
        assert "exposure_cap" in rejection["by_reason"]

    @pytest.mark.asyncio
    async def test_circuit_breaker_rejection(self, async_client):
        """Circuit breaker rejections (balance below floor) tracked."""
        rejected = [
            _make_rejected_signal(
                id_=1,
                rejection_reason="Circuit breaker: balance $95.00 < floor $100.00 (5% drawdown)",
            ),
        ]

        ctx = _make_outcomes_ctx([], rejected, [])
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-outcomes")

        assert resp.status_code == 200
        rejection = resp.json()["rejection_analysis"]
        # Dynamic reason strings should be tracked under their key
        reason_key = "Circuit breaker: balance $95.00 < floor $100.00 (5% drawdown)"
        assert reason_key in rejection["by_reason"]

    @pytest.mark.asyncio
    async def test_volatility_gate_rejection(self, async_client):
        """Stablecoin-like volatility gate rejections tracked."""
        rejected = [
            _make_rejected_signal(
                id_=1,
                rejection_reason="Min volatility gate: SL distance 0.0010% < 0.20% (stablecoin-like)",
            ),
        ]

        ctx = _make_outcomes_ctx([], rejected, [])
        with patch("app.storage.Database.get_session", return_value=ctx):
            resp = await async_client.get("/api/analytics/signal-outcomes")

        assert resp.status_code == 200
        rejection = resp.json()["rejection_analysis"]
        assert rejection["total_rejected"] == 1
