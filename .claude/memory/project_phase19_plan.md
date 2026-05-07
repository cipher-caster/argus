---
name: Phase 19 — Win Rate Trend (BUILT THEN REMOVED)
description: Phase 19 was fully built in v1.1.0 then completely removed in commit 70074ed. Do not treat as unstarted work.
type: project
originSessionId: e8dc91a7-8713-485f-bd3f-8e7acb71133b
---
Phase 19 (daily win-rate snapshot) was **built and then fully ripped out**. It is NOT pending work.

**What was built (v1.1.0, 2026-04-09):**
- `signal_outcome_snapshot` table + `migrate_v0_19_0.py` migration
- `snapshot_signal_outcomes` arq cron job (00:05 UTC) — idempotent daily aggregation
- `/api/analytics/signal-outcomes/trend` endpoint with 1hr Redis cache
- `WinRateTrend.tsx` SVG chart wired as 3rd analytics tab (Best Setups / Signal Log / Win Rate Trend)

**What was removed (commit 70074ed, 2026-04-17):**
All of the above was deleted end-to-end — frontend component, tab, hook, API client, types, backend endpoint, snapshot job, schema, migration, and tests. Commit message: "Drop the analytics Win Rate Trend panel and its backend support." All 399 backend tests passed post-removal.

**Why removed:** Not stated explicitly in commit message; removal was clean and deliberate.

**Current state:** Analytics has 2 tabs only (Best Setups, Signal Log). No snapshot table exists in the DB. No trend endpoint exists.

**Why:** Any agent reading old plans or the v1.1.0 changelog must know Phase 19 is over and gone, not pending.
**How to apply:** Do not re-implement WinRateTrend or the snapshot job unless the user explicitly requests it. Do not reference docs/PHASE19_PLAN.md as an active plan — it describes a feature that was removed.
