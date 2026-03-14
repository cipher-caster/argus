# Dashboard & Analytics Improvement Plan

Professional-grade upgrades ordered by impact vs effort. Each item is self-contained — complete one, commit, then move to the next.

---

## ✅ Item 1 — Oracle Score Column in CoinTable
**Status: DONE (v0.5.5)**

Added `ScoreBadge` component to `/markets` CoinTable. Fetches `useOracleScreener("1h", 50)`, maps symbol → score, shows colored badge (+4 to -4) with tooltip showing bias, state, and advice. Shows `—` for coins outside top 50.

---

## ✅ Item 2 — Backtest Win Rate on Best Setups Cards
**Status: DONE (v0.5.6)**

Surfaced Oracle backtest stats (`win_rate`, `total_trades`) on each Best Setups card.

**Implementation:**
- Added `win_rate: Optional[float]` and `total_trades: Optional[int]` to `BestSetupItem` schema (both default `None`)
- In `get_best_setups()`, after the conviction filter produces ≤10 coins, fetches 1h + 1d candles for those coins and runs `oracle.analyze()` to get backtest performance
- Both fields remain `None` when `total_trades < 10` (sample too small to be meaningful)
- Frontend shows a colored badge (`XX% hist.`) in the bottom-right of each card, or `— hist.` when data is insufficient

**Thresholds (based on 2:1 RR math — break-even = 33.3%):**
- ≥ 50% → green (solidly profitable)
- 33–49% → yellow (marginal but above break-even)
- < 33% → red (below break-even, losing on this coin)

**Files changed:**
- `backend/app/schemas/analytics.py`
- `backend/app/routes/analytics.py`
- `frontend/src/lib/api.ts`
- `frontend/src/components/analytics/BestSetups.tsx`

---

## ✅ Item 3 — Multi-Timeframe Confirmation on Best Setups (Eliz + Mayne Framework)
**Status: DONE (v0.5.7)**

MTF confluence based on the Eliz (@eliz883) + Trader Mayne (@Tradermayne) framework used in Walsh Wealth / WealthGroup circles:

- **Eliz lane** → 4H (entry trigger) + 1D (swing structure). Intermediate setups.
- **Mayne lane** → 12H (higher-TF bias) + 1W (macro/weekly direction). Big-picture filter.

When all four align → full confluence, highest-conviction swing trade.
When only Eliz aligns → intermediate setup, treat as shorter-duration.
When only Mayne aligns → macro bias present but no near-term trigger yet.

**Implementation:**
- Added `timeframe_confirmation: Optional[Dict[str, bool]]` to `BestSetupItem` schema
- In `get_best_setups()`, after filtering ≤10 coins, fetches 1d/12h/1w candles concurrently (4h reuses already-fetched `titan_candles`)
- Runs Titan on each TF; "confirmed" = Titan signal matches setup direction (BUY/BUY_LIMIT for LONG, SELL/SELL_LIMIT for SHORT)
- Frontend shows two grouped badge rows: `Eliz: 4H 1D` and `Mayne: 12H 1W` — green when confirmed, gray when not

**Files changed:**
- `backend/app/schemas/analytics.py`
- `backend/app/routes/analytics.py`
- `frontend/src/lib/api.ts`
- `frontend/src/components/analytics/BestSetups.tsx`

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
✅ Item 1 → ✅ Item 2 → ✅ Item 3 → Item 4 → ✅ Item 5
```

Item 4 is the remaining large item — needs a DB migration and worker job (~1 day).
Item 5 (tests) is done and can be extended incrementally alongside any of the above.
