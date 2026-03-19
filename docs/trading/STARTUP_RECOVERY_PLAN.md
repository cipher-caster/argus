# Startup Recovery & Activity Log Plan

**Status:** IN PROGRESS — 2026-03-19

## Problem

When the user closes Argus (docker-compose down) and reopens hours/days later:
1. Missed 4H candle close scans — signals lost forever
2. Open signals/positions not monitored — TP/SL could have been hit during downtime
3. No visibility into what happened or was missed
4. Both signal resolution and position management use current ticker price only — if price spiked through TP during downtime and came back, it's never recorded

## Solution: 4 Components

### Component 1: Worker Heartbeat + Gap Detection

**Redis key:** `worker:heartbeat` — updated every cron cycle with current timestamp.

On startup:
1. Read `worker:heartbeat` from Redis
2. If missing → first boot, skip recovery
3. If present → calculate gap duration and which 4H candle closes were missed
4. 4H close times: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC

### Component 2: Startup Recovery Job

New function `recover_missed_signals(ctx)` called during `startup()`:

```
For each missed 4H candle close:
  1. Fetch 4H candles for each watchlist coin (data exists on Binance regardless of our uptime)
  2. Run Titan + Oracle analysis on the candle state at that close
  3. If signal qualifies → insert to signal_log with fired_at = candle close time
  4. Log activity: "Recovered BTC LONG signal from 16:00 candle close"
```

Then run:
- `resolve_signal_outcomes_historical()` — uses candle high/low instead of current price
- `execute_signals()` — convert recovered signals to paper trades
- `manage_positions()` — check fills and exits

### Component 3: Historical TP/SL Resolution

New function `resolve_outcomes_with_candles()`:

For each OPEN signal/position during recovery:
1. Fetch candles from `fired_at` to now
2. Walk each candle chronologically:
   - LONG: if `candle.high >= tp` → WIN (resolved_at = candle timestamp)
   - LONG: if `candle.low <= sl` → LOSS
   - If both hit in same candle: use candle open direction to determine which hit first
     - If open > close (bearish candle) → SL likely hit first
     - If open < close (bullish candle) → TP likely hit first
3. Same logic inverted for SHORT

This replaces the current "check current ticker price" approach during recovery only.
Normal real-time resolution continues using ticker price (good enough for 5-min checks).

### Component 4: Activity Log

**New table: `activity_log`**
- `id` — auto-increment PK
- `timestamp` — BigInteger (epoch ms)
- `event_type` — String: STARTUP, SHUTDOWN, RECOVERY_SCAN, SIGNAL_RECOVERED, OUTCOME_RESOLVED, POSITION_RECOVERED, HEARTBEAT_GAP, ERROR
- `details` — JSON (flexible payload: symbol, direction, gap_hours, signals_found, etc.)
- `severity` — String: INFO, WARN, ERROR

**API:** `GET /api/system/activity-log?limit=50&type=RECOVERY_SCAN`

**Frontend:** `ActivityFeed` component showing recent system events:
- On the Trading page (sidebar or below positions)
- On the Dashboard (compact widget)
- Color-coded by severity, newest first
- Shows: "Recovered 3 missed scans (6h gap)", "BTC LONG signal recovered from 16:00 close", "ETH position SL hit during downtime @ $2,100"

## Implementation Order

1. Activity Log schema + API (no dependencies)
2. Worker heartbeat (simple Redis set/get)
3. Startup recovery job (depends on 1 + 2)
4. Historical TP/SL resolution (depends on 3)
5. Frontend ActivityFeed component (depends on 1)
6. Add execute_signals to startup sequence (quick win, no dependencies)

## Files to Create/Modify

- **Create:** `backend/app/schemas/activity_log.py` — ActivityLog model
- **Create:** `backend/app/routes/system.py` — activity log API
- **Create:** `frontend/src/components/features/trading/ActivityFeed.tsx` — UI component
- **Modify:** `backend/app/worker.py` — heartbeat, recovery job, startup sequence
- **Modify:** `backend/app/jobs/signal_log.py` — historical resolution function
- **Modify:** `backend/app/storage.py` — register ActivityLog table
- **Modify:** `backend/app/main.py` — register system router
- **Modify:** `frontend/src/lib/api.ts` — activity log types + fetch
- **Modify:** frontend trading/dashboard pages — add ActivityFeed
