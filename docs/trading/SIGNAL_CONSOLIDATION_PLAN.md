# Signal Consolidation Plan

> Problem: ActiveSetups, BestSetups, and TitanSignalsPanel show ephemeral live scan signals
> that are never logged to the database. We can't track outcomes or optimize what isn't measured.
> The signal_log worker only logs 11 watchlist coins at 4H candle closes.
> The live scanners cover 50 coins on-demand but write zero rows.

---

## Changes

### 1. Backend: Add `log_best_setups` worker job (NEW)
**File:** `backend/app/jobs/signal_log.py` — add new function

Piggyback on the `sync_analytics_cache` warm cycle (runs every 5 min).
After best-setups cache is warmed, read the cached result from Redis
(`analytics:best-setups:4h:50`) and write qualifying signals to `signal_log`
with `source='scanner'`.

- Uses the same dedup as `log_watchlist_setups`: `ON CONFLICT DO NOTHING`
  on `(symbol, direction) WHERE outcome='OPEN'`
- Only logs signals with conviction >= 60 (avoid noise)
- The existing `resolve_signal_outcomes` job automatically picks them up
  for WIN/LOSS/REVIEW resolution every 30 min

**File:** `backend/app/worker.py` — add cron for `log_best_setups`
- Schedule: `minute={3, 8, 13, 18, 23, 28, 33, 38, 43, 48, 53, 58}` (1 min after cache warm)

### 2. Frontend: Remove Titan Signals tab from analytics
**File:** `frontend/src/app/analytics/page.tsx`
- Remove TitanSignalsPanel dynamic import
- Remove "titan-signals" from MENU_ITEMS and CHART_INFO
- Remove the `{activeTab === "titan-signals" && ...}` render line

### 3. Frontend: Delete orphaned components
**Delete:** `frontend/src/components/analytics/TitanSignalsPanel.tsx`
**Delete:** `frontend/src/components/analytics/TitanRadar.tsx`
- TitanRadar is exported from barrel but never rendered on any page
- Check barrel index (`frontend/src/components/analytics/index.ts`) and remove exports

### 4. Frontend: Add 'Scanner' source filter to SignalLog
**File:** `frontend/src/components/analytics/SignalLog.tsx`
- Change `SOURCES` from `["All", "Live", "Backtest"]` to `["All", "Live", "Scanner", "Backtest"]`
- Add scanner badge styling (purple/violet to distinguish from live blue and backtest amber)

### 5. Update SignalLog description
**File:** `frontend/src/app/analytics/page.tsx`
- Update the CHART_INFO signal-log description to mention scanner signals

---

## What NOT to touch
- `/api/strategy/titan/{symbol}` endpoint — chart deep-dive modal depends on it
- `/api/analytics/titan-radar` endpoint — keep as internal API, just remove the UI tab
- ActiveSetups dashboard component — keep as-is (real-time scanner view)
- ActiveSignals dashboard component — keep as-is (tracks OPEN signal log entries)
- BestSetups analytics tab — keep (full view of what ActiveSetups shows compact)
- CoinAnalysisModal — uses Titan strategy API directly, unrelated

---

## File Summary

| Action | File |
|--------|------|
| Modify | `backend/app/jobs/signal_log.py` — add `log_best_setups()` |
| Modify | `backend/app/worker.py` — add cron + import |
| Modify | `frontend/src/app/analytics/page.tsx` — remove Titan tab |
| Delete | `frontend/src/components/analytics/TitanSignalsPanel.tsx` |
| Delete | `frontend/src/components/analytics/TitanRadar.tsx` |
| Modify | `frontend/src/components/analytics/index.ts` — remove exports |
| Modify | `frontend/src/components/analytics/SignalLog.tsx` — add Scanner filter |

---

## Verification
1. `docker compose logs -f worker` shows `log_best_setups` firing every 5 min
2. Signal Log tab shows new signals with `source=scanner` badge
3. Scanner filter button works
4. Titan Signals tab is gone from analytics sidebar
5. Chart deep-dive modal still works (uses separate Titan strategy API)
6. ActiveSetups and ActiveSignals dashboard widgets unaffected
