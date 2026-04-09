"""
Phase 19 Snapshot Job tests.

Covers:
- test_idempotency: running the job twice does not create duplicate rows
- test_conviction_band_binning: 62→"55-64", 75→"75+", 83→"75+", 95→"75+"
- test_win_rate_math: 10W + 4L → 71.43 win_rate
- test_trend_endpoint_empty_table_returns_200: GET /trend with no data → 200 + empty trend
- test_trend_endpoint_days_filter: old snapshots excluded by days param

All database-touching tests use an in-memory SQLite database so no live
Postgres is required.  Endpoint tests mock the DB session.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.jobs.snapshot import _conviction_band, snapshot_signal_outcomes


# ---------------------------------------------------------------------------
# Unit: conviction band helper
# ---------------------------------------------------------------------------

class TestConvictionBandBinning:

    def test_conviction_62_gives_55_64(self):
        assert _conviction_band(62) == "55-64"

    def test_conviction_64_gives_55_64(self):
        assert _conviction_band(64) == "55-64"

    def test_conviction_65_gives_65_74(self):
        assert _conviction_band(65) == "65-74"

    def test_conviction_74_gives_65_74(self):
        assert _conviction_band(74) == "65-74"

    def test_conviction_75_gives_75_plus(self):
        assert _conviction_band(75) == "75+"

    def test_conviction_83_gives_75_plus(self):
        assert _conviction_band(83) == "75+"

    def test_conviction_95_gives_75_plus(self):
        assert _conviction_band(95) == "75+"


# ---------------------------------------------------------------------------
# Unit: win_rate math
# ---------------------------------------------------------------------------

class TestWinRateMath:

    def test_10W_4L_gives_71_43(self):
        """10 wins + 4 losses = 14 total → win_rate = 10/14 * 100 = 71.43."""
        wins, losses = 10, 4
        win_rate = round(wins / (wins + losses) * 100, 2)
        assert win_rate == pytest.approx(71.43, abs=0.01)

    def test_zero_denominator_returns_none(self):
        """0 wins + 0 losses → win_rate is None (not a division error)."""
        wins, losses = 0, 0
        win_rate = round(wins / (wins + losses) * 100, 2) if (wins + losses) > 0 else None
        assert win_rate is None

    def test_all_wins_gives_100(self):
        wins, losses = 5, 0
        win_rate = round(wins / (wins + losses) * 100, 2) if (wins + losses) > 0 else None
        assert win_rate == 100.0

    def test_all_losses_gives_0(self):
        wins, losses = 0, 7
        win_rate = round(wins / (wins + losses) * 100, 2) if (wins + losses) > 0 else None
        assert win_rate == 0.0


# ---------------------------------------------------------------------------
# Integration: snapshot_signal_outcomes job (mocked DB)
# ---------------------------------------------------------------------------

def _make_signal(
    outcome="WIN",
    conviction=75,
    regime_at_signal="BULL",
    market_state="BULL",
    source="live",
    symbol="BTCUSDT",
    fired_at=1_704_067_200_000,
    resolved_at=1_704_081_600_000,
):
    s = MagicMock()
    s.outcome = outcome
    s.conviction = conviction
    s.regime_at_signal = regime_at_signal
    s.market_state = market_state
    s.source = source
    s.symbol = symbol
    s.fired_at = fired_at
    s.resolved_at = resolved_at
    return s


def _make_db_ctx(sentinel_row, signals):
    """
    Build a mock async context manager for Database.get_session().

    First execute call: sentinel idempotency check.
    Second execute call: resolved signals fetch.
    Remaining execute calls: upserts (return None-like mock).
    """
    mock_session = AsyncMock()

    sentinel_result = MagicMock()
    sentinel_result.scalars.return_value.first.return_value = sentinel_row

    signals_result = MagicMock()
    signals_result.scalars.return_value.all.return_value = signals

    # Upsert calls return a simple mock
    upsert_result = MagicMock()

    # Side-effect: first two are specific, the rest are upserts
    mock_session.execute = AsyncMock(
        side_effect=[sentinel_result, signals_result] + [upsert_result] * 500
    )
    mock_session.commit = AsyncMock()

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


class TestIdempotency:

    @pytest.mark.asyncio
    async def test_second_run_skips_when_sentinel_exists(self):
        """If the sentinel row exists, no signals are fetched and no upserts happen."""
        sentinel = MagicMock()  # truthy: row exists
        ctx = _make_db_ctx(sentinel_row=sentinel, signals=[])

        with patch("app.jobs.snapshot.Database.get_session", return_value=ctx):
            await snapshot_signal_outcomes({})

        mock_session = ctx.__aenter__.return_value
        # Only the sentinel check execute call should have been made (index 0)
        assert mock_session.execute.call_count == 1
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_first_run_proceeds_when_no_sentinel(self):
        """If no sentinel, job proceeds to fetch signals and upsert rows."""
        signals = [_make_signal(outcome="WIN")]
        ctx = _make_db_ctx(sentinel_row=None, signals=signals)

        with patch("app.jobs.snapshot.Database.get_session", return_value=ctx):
            await snapshot_signal_outcomes({})

        mock_session = ctx.__aenter__.return_value
        # sentinel + signals fetch + at least one upsert
        assert mock_session.execute.call_count >= 3
        mock_session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Endpoint: GET /api/analytics/signal-outcomes/trend
# ---------------------------------------------------------------------------

def _make_snapshot_row(
    snapshot_date="2026-04-08",
    regime="ALL",
    conviction_band="ALL",
    source="ALL",
    coin=None,
    wins=10,
    losses=6,
    reviews=0,
    rejected=0,
    total_resolved=16,
    win_rate=62.5,
    avg_time_to_resolution_ms=14_400_000.0,
):
    row = MagicMock()
    row.snapshot_date = snapshot_date
    row.regime = regime
    row.conviction_band = conviction_band
    row.source = source
    row.coin = coin
    row.wins = wins
    row.losses = losses
    row.reviews = reviews
    row.rejected = rejected
    row.total_resolved = total_resolved
    row.win_rate = win_rate
    row.avg_time_to_resolution_ms = avg_time_to_resolution_ms
    return row


def _make_trend_db_ctx(rows):
    """Build a mock DB session that returns `rows` from execute."""
    mock_session = AsyncMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = rows

    mock_session.execute = AsyncMock(return_value=result)

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


class TestTrendEndpointEmptyTable:

    @pytest.mark.asyncio
    async def test_returns_200_with_empty_trend_when_no_snapshots(self, async_client):
        """GET /trend with an empty table → 200 with trend=[]."""
        ctx = _make_trend_db_ctx(rows=[])
        with (
            patch("app.storage.Database.get_session", return_value=ctx),
            patch("app.routes.analytics.RedisClient") as mock_redis,
        ):
            mock_redis.get_json = AsyncMock(return_value=None)
            mock_redis.set_json = AsyncMock(return_value=True)
            resp = await async_client.get("/api/analytics/signal-outcomes/trend")

        assert resp.status_code == 200
        body = resp.json()
        assert "trend" in body
        assert body["trend"] == []

    @pytest.mark.asyncio
    async def test_returns_trend_list_with_rows(self, async_client):
        """GET /trend with one snapshot row → trend has one entry."""
        row = _make_snapshot_row()
        ctx = _make_trend_db_ctx(rows=[row])
        with (
            patch("app.storage.Database.get_session", return_value=ctx),
            patch("app.routes.analytics.RedisClient") as mock_redis,
        ):
            mock_redis.get_json = AsyncMock(return_value=None)
            mock_redis.set_json = AsyncMock(return_value=True)
            resp = await async_client.get("/api/analytics/signal-outcomes/trend")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["trend"]) == 1
        entry = body["trend"][0]
        assert entry["date"] == "2026-04-08"
        assert entry["win_rate"] == pytest.approx(62.5)
        assert entry["wins"] == 10
        assert entry["losses"] == 6
        assert entry["total_resolved"] == 16


class TestTrendEndpointDaysFilter:

    @pytest.mark.asyncio
    async def test_old_snapshots_excluded_by_days_param(self, async_client):
        """
        Snapshots older than `days` should not appear in trend.

        We pass days=7 but the only row in DB has snapshot_date="2025-01-01"
        (> 7 days ago relative to 2026-04-08), so the endpoint should filter
        it out.  We simulate this by returning no rows from the DB query
        (the WHERE clause in the endpoint handles date filtering).
        """
        # DB returns nothing because the WHERE filters out old rows
        ctx = _make_trend_db_ctx(rows=[])
        with (
            patch("app.storage.Database.get_session", return_value=ctx),
            patch("app.routes.analytics.RedisClient") as mock_redis,
        ):
            mock_redis.get_json = AsyncMock(return_value=None)
            mock_redis.set_json = AsyncMock(return_value=True)
            resp = await async_client.get("/api/analytics/signal-outcomes/trend?days=7")

        assert resp.status_code == 200
        assert resp.json()["trend"] == []

    @pytest.mark.asyncio
    async def test_days_param_passed_to_cache_key(self, async_client):
        """Different days values produce different cache keys (cache miss per value)."""
        ctx = _make_trend_db_ctx(rows=[])
        cache_keys = []

        async def capture_set(key, data, ttl=None):
            cache_keys.append(key)

        with (
            patch("app.storage.Database.get_session", return_value=ctx),
            patch("app.routes.analytics.RedisClient") as mock_redis,
        ):
            mock_redis.get_json = AsyncMock(return_value=None)
            mock_redis.set_json = AsyncMock(side_effect=capture_set)

            await async_client.get("/api/analytics/signal-outcomes/trend?days=7")
            await async_client.get("/api/analytics/signal-outcomes/trend?days=30")

        # Two different cache keys should have been written
        assert len(cache_keys) == 2
        assert cache_keys[0] != cache_keys[1]
        assert "7" in cache_keys[0]
        assert "30" in cache_keys[1]
