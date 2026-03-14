# Dashboard & Analytics Improvement Plan

Professional-grade upgrades ordered by impact vs effort. Each item is self-contained — complete one, commit, then move to the next.

---

## ✅ Item 1 — Oracle Score Column in CoinTable
**Status: DONE (v0.5.5)**

Added `ScoreBadge` component to `/markets` CoinTable. Fetches `useOracleScreener("1h", 50)`, maps symbol → score, shows colored badge (+4 to -4) with tooltip showing bias, state, and advice. Shows `—` for coins outside top 50.

---

## Item 2 — Backtest Win Rate on Best Setups Cards
**Files:**
- `backend/app/routes/analytics.py` — `get_best_setups()` endpoint
- `backend/app/schemas/analytics.py` — `BestSetupItem` schema
- `frontend/src/components/analytics/BestSetups.tsx`
- `frontend/src/lib/api.ts`

The Oracle strategy already runs a backtest and returns `performance.win_rate` and `performance.net_profit`. The best-setups endpoint currently discards this data. Surface it on each card.

- Add `win_rate: float` and `total_trades: int` fields to `BestSetupItem`
- In `get_best_setups()`, fetch Oracle strategy data per coin to get backtest stats
- On each setup card show: `"Historical: 29% win rate (17 trades)"` with color coding:
  - ≥50% → green, 35–50% → yellow, <35% → red

**Result:** Every setup card shows whether the strategy has actually worked on that coin historically.

---

## Item 3 — Multi-Timeframe Confirmation on Best Setups
**Files:**
- `backend/app/routes/analytics.py` — `get_best_setups()` endpoint
- `backend/app/schemas/analytics.py` — `BestSetupItem` schema
- `frontend/src/components/analytics/BestSetups.tsx`
- `frontend/src/lib/api.ts`

A setup confirmed on 1H + 4H + 1D is far stronger than one on a single timeframe. We already call Oracle and Titan per coin — extend this to run on all three timeframes.

- Add `timeframe_confirmation: { "1h": bool, "4h": bool, "1d": bool }` to `BestSetupItem`
- In `get_best_setups()`, run Titan on 1h, 4h, and 1d candles per coin
- On setup cards show: `1H ✓  4H ✓  1D ✗` — confirmed timeframes in green, unconfirmed in gray

**Result:** You can immediately see if a setup is a quick scalp (1H only) or a swing trade (all three aligned).

---

## Item 4 — Signal History Log
**Files:**
- `backend/app/models/` — new `SignalLog` database model
- `backend/app/routes/analytics.py` — new `/api/analytics/signal-log` endpoint
- `backend/app/worker.py` — periodic job to check best-setups and log new signals
- `frontend/src/components/analytics/` — new `SignalHistory.tsx` component
- `frontend/src/app/analytics/page.tsx` — add tab

Track every time a high-conviction setup fires and record whether it hit TP or SL.

- Worker job runs every 30 min: calls best-setups, compares to last logged signals, inserts new ones into Postgres
- Each log entry: `symbol, direction, conviction, entry, tp, sl, fired_at`
- Follow-up job (24h later): checks if price hit TP or SL, updates `outcome` column
- Frontend shows a table: Signal | Direction | Fired At | Entry | TP | SL | Outcome (WIN/LOSS/OPEN)

**Result:** After a few weeks you'll know if Oracle+Titan is actually profitable on your specific coins. This is the foundation for trusting or tuning the system.

---

## Item 5 — Test Scripts
**Files:**
- `backend/tests/test_analytics.py` — endpoint tests
- `backend/tests/test_oracle.py` — Oracle strategy unit tests
- `backend/tests/test_titan.py` — Titan strategy unit tests
- `frontend/src/tests/` — component and hook tests

The system has no automated tests. Every change is currently verified manually. Adding a baseline test suite prevents regressions when tuning strategies or adding features.

### Backend (pytest)

```
backend/tests/
  test_analytics.py     — /api/analytics/screener, /best-setups, /signal-summary
  test_oracle.py        — OracleStrategy.analyze() output shape, score bounds (-4 to +4), bias values
  test_titan.py         — TitanStrategy.analyze() returns valid signal enum, confidence in 0-100
  test_market.py        — /api/market/coins, /api/market/tickers response shape
  conftest.py           — shared fixtures: mock OHLCV data, mock Redis cache
```

Key cases to cover:
- Oracle score is always in range [-4, +4]
- Titan signal is always one of: BUY, SELL, WAIT_OB, WAIT_OS, BUY_LIMIT, SELL_LIMIT
- `best-setups` only returns coins where abs(oracle_score) ≥ 2 AND titan confidence ≥ 55%
- `signal-summary` market_state is one of: STRONG BULL, STRONG BEAR, NEUTRAL, SLEEPING
- All endpoints return within 5s (integration test against running Docker stack)

### Frontend (Vitest + Testing Library)

```
frontend/src/tests/
  components/ActiveSetups.test.tsx   — renders setups, empty state, loading skeletons
  components/BTCCard.test.tsx        — renders price, handles missing data without crashing
  components/DashboardStatusBar.test.tsx — renders all 4 stat sections
  hooks/useAnalyticsData.test.ts     — query key structure, staleTime values
```

### Running tests

```bash
# Backend
docker compose exec backend pytest tests/ -v

# Single test file
docker compose exec backend pytest tests/test_analytics.py -v

# Frontend
cd frontend && npm run test
```

**Result:** Regressions caught automatically. Confidence to tune Oracle/Titan parameters without breaking the UI layer.

---

## Order of Execution

```
Item 2 → Item 3 → Item 4 → Item 5
```

Items 2–3 are backend additions with UI changes (~2–4 hours each).
Item 4 is the largest — needs a DB migration and worker job (~1 day).
Item 5 (tests) can be done incrementally alongside any of the above — start with backend unit tests since they're fastest to write and highest value.
