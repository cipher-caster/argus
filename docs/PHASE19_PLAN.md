# Phase 19: Daily Signal Outcome Snapshot

**Status:** Planned — not started
**Priority:** Tier 3 (after Phase 18 data model, which is complete)
**Effort:** Medium
**Depends on:** Phase 17 (tests ✓), Phase 18 (data model ✓)

---

## Goal

Replace the on-the-fly `GET /api/analytics/signal-outcomes` computation with a daily snapshot job that persists aggregated win-rate statistics to a DB table. Enables queries like "win rate last week vs this week" and a trend chart on the analytics page.

---

## New DB Table: `SignalOutcomeSnapshot`

**File:** `backend/app/schemas/snapshot.py`

Each row = one dimension slice per day: `(snapshot_date, regime, conviction_band, source, coin)`.

```python
class SignalOutcomeSnapshot(SQLModel, table=True):
    __tablename__ = "signal_outcome_snapshot"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Slice dimensions
    snapshot_date: str           # ISO string "2026-03-30" — sortable, no tz issues
    regime: str                  # "BULL" | "BEAR" | "UNKNOWN" | "ALL"
    conviction_band: str         # "60-69" | "70-79" | "80-89" | "90-100" | "ALL"
    source: str                  # "live" | "scanner" | "backtest" | "ALL"
    coin: Optional[str]          # NULL = aggregate row; "BTCUSDT" = per-coin row

    # Outcome counts
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    reviews: int = Field(default=0)
    rejected: int = Field(default=0)
    total_resolved: int          # wins + losses (denominator for win_rate)

    # Derived
    win_rate: Optional[float]    # NULL when total_resolved == 0
    avg_time_to_resolution_ms: Optional[int]

    snapshotted_at: int = Field(sa_type=BigInteger)  # epoch ms

    __table_args__ = (
        # Partial unique index for per-coin rows
        Index("uq_snapshot_slice", "snapshot_date", "regime", "conviction_band", "source", "coin",
              unique=True, postgresql_where=text("coin IS NOT NULL")),
        # Partial unique index for aggregate rows
        Index("uq_snapshot_aggregate", "snapshot_date", "regime", "conviction_band", "source",
              unique=True, postgresql_where=text("coin IS NULL")),
    )
```

**Design decisions:**
- `snapshot_date` as VARCHAR string — avoids asyncpg timezone serialization issues
- `regime="ALL"` / `conviction_band="ALL"` sentinel rows — top-level aggregate, default chart view
- Per-coin rows (`coin != NULL`) + aggregate rows (`coin IS NULL`) in same table
- `reviews` and `rejected` stored (not computed) — tracks signal quality drift over time
- `win_rate=NULL` (not 0%) when `total_resolved == 0` — frontend renders as a gap, not a zero

---

## Implementation Steps

| Step | Task | File |
|------|------|------|
| 1 | `SignalOutcomeSnapshot` SQLModel table | `backend/app/schemas/snapshot.py` (new) |
| 2 | Register in `create_tables()` | `backend/app/storage.py` |
| 3 | Migration script | `backend/migrate_v0_19_0.py` (new) |
| 4 | `snapshot_signal_outcomes` arq job | `backend/app/jobs/snapshot.py` (new) |
| 5 | Register job + cron in worker | `backend/app/worker.py` |
| 6 | `GET /api/analytics/signal-outcomes/trend` endpoint | `backend/app/routes/analytics.py` |
| 7 | Types + fetcher | `frontend/src/lib/api.ts` |
| 8 | `useSignalOutcomeTrend` hook | `frontend/src/hooks/useAnalyticsData.ts` |
| 9 | `WinRateTrend.tsx` chart component | `frontend/src/components/analytics/` (new) |
| 10 | Wire into analytics page as new tab | `frontend/src/app/analytics/page.tsx` |
| 11 | Tests | `backend/tests/test_snapshot_job.py` (new) |

---

## Job: `snapshot_signal_outcomes`

**File:** `backend/app/jobs/snapshot.py`
**Schedule:** Daily at 00:05 UTC (5 min after `resolve_signal_outcomes` runs at 00:00)

**Algorithm:**
1. `snapshot_date = datetime.utcnow().date().isoformat()`
2. Idempotency check — if aggregate row for today exists, return early (fast path)
3. Query all `SignalLog` rows where `outcome IN ("WIN", "LOSS", "REVIEW", "REJECTED")`
4. Build dimension slices by (regime, conviction_band, source, coin)
5. Compute `win_rate` and `avg_time_to_resolution_ms` per slice
6. Bulk-insert via `pg_insert().on_conflict_do_update()` — re-run on same day refreshes rather than errors
7. Commit in one transaction

**Worker registration** (`backend/app/worker.py`):
```python
from app.jobs.snapshot import snapshot_signal_outcomes

# In WorkerSettings:
cron(snapshot_signal_outcomes, hour={0}, minute={5}),
```

---

## API Endpoint

`GET /api/analytics/signal-outcomes/trend?days=30&regime=ALL&source=ALL`

**Response:**
```json
{
  "trend": [
    { "date": "2026-03-01", "win_rate": 63.2, "total_resolved": 19, "wins": 12, "losses": 7, "avg_ttf_hours": 18.4 }
  ],
  "regime_breakdown": [
    { "date": "2026-03-01", "regime": "BULL", "win_rate": 71.0, "total_resolved": 14 },
    { "date": "2026-03-01", "regime": "BEAR", "win_rate": 40.0, "total_resolved": 5 }
  ],
  "conviction_breakdown": [
    { "date": "2026-03-01", "conviction_band": "80-89", "win_rate": 75.0, "total_resolved": 8 }
  ]
}
```

**Caching:** Redis, 1hr TTL, key `analytics:signal-outcomes-trend:{days}:{regime}:{conviction_band}:{source}:{coin}`

---

## Frontend: `WinRateTrend.tsx`

- New **"Win Rate Trend"** tab on analytics page
- SVG line chart (same pattern as `EquityCurve.tsx`) — no new dependencies
- Dual lines: overall win rate + selected regime or conviction band overlay
- 50% baseline dashed line
- Filter pills: [BULL | BEAR | ALL] regime, conviction band selector
- Stat cards: 30d avg win rate, best day, trend direction arrow
- Empty state: "No snapshot data yet — first snapshot runs at 00:05 UTC"

**Hook** (`useAnalyticsData.ts`):
```typescript
export function useSignalOutcomeTrend(days = 30, regime?: string, conviction_band?: string, source = "ALL", coin?: string) {
  return useQuery({
    queryKey: ["analytics", "signal-outcomes-trend", days, regime, conviction_band, source, coin],
    queryFn: () => fetchSignalOutcomeTrend(days, regime, conviction_band, source, coin),
    staleTime: 60 * 60_000,  // 1 hour
    gcTime: 2 * 60 * 60_000,
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
  });
}
```

---

## Tests (5)

| Test | What it checks |
|------|----------------|
| `test_snapshot_idempotency` | Second run for same date skips re-insert |
| `test_snapshot_conviction_bands` | Convictions 62/75/83/95 land in correct bands |
| `test_snapshot_win_rate_calculation` | 10W + 4L → `win_rate = 71.4` |
| `test_trend_endpoint_empty` | Empty table returns `{trend: []}`, not 500 |
| `test_trend_endpoint_date_filter` | `days=1` returns only today's snapshot |

---

## Gotchas

- **Small sample sizes:** `win_rate=NULL` not `0%` — frontend must render as line gap
- **Partial unique indexes:** Need separate `Index` objects with `postgresql_where=text(...)` — proven pattern in `SignalLog` model (`uq_signal_log_open`)
- **Timezone:** Use `datetime.utcnow()` not `datetime.now()` in job; string comparison on `YYYY-MM-DD` sorts correctly
