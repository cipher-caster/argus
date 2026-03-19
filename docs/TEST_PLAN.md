# Argus Test Plan — Preventing Regressions at Scale

## Current State (v0.8.1, 2026-03-19)

| Layer | Tests | Coverage |
|-------|-------|----------|
| Backend unit (pytest) | 230 | Signal log, trading engine, risk manager, strategies, analytics, routes |
| Frontend E2E (Playwright) | 7 | Basic page loads + navigation only |
| Frontend component | 0 | No component test framework installed |
| TypeScript | `tsc --noEmit` | Type safety only, no runtime tests |

### What's Tested (Backend)

| Module | File | Tests | Risk Level |
|--------|------|-------|------------|
| Signal pipeline | `test_signal_log.py` | 28 | Covered |
| Trading engine | `test_trading.py` | 42 | Covered |
| Trading routes | `test_trading_routes.py` | 18 | Covered |
| Oracle strategy | `test_oracle.py` | 30 | Covered |
| Titan strategy | `test_titan.py` | 20 | Covered |
| Signal log stats | `test_analytics_stats.py` | 7 | Covered |
| Optimization | `test_optimization_routes.py` | 7 | Covered |
| Indicator routes | `test_indicator_routes.py` | 10 | Covered |
| Analytics | `test_analytics_*.py` | 30+ | Covered |
| Market/worker | `test_market.py`, `test_worker.py` | 10+ | Covered |

### What's NOT Tested

**Backend gaps:**
- `TradeAnalyzer` internal logic (only route-level mocks, not real aggregation)
- `backtest_engine.py` — the core backtester has no unit tests
- `resolve_outcomes_historical` — candle-walk logic (simultaneous TP/SL, same-candle inference)
- Worker job scheduling/registration (`worker.py`)
- Notification system (`notifier.py`)

**Frontend gaps:**
- No component tests — a renamed prop or changed API shape silently breaks rendering
- E2E only covers navigation — no data verification, no trading page, no analytics tabs
- No error state testing (API down, empty data, stale cache)

---

## Phase A: Backend Safety Net (Priority 1 — prevents silent breakage)

### A1: Backtest Engine Unit Tests (~8 tests)
**File:** `test_backtest_engine.py`
**Why:** This is the optimization foundation. A bug here silently corrupts all sweep results.

- `test_long_win_outcome` — price hits TP → WIN, correct R calculation
- `test_long_loss_outcome` — price hits SL → LOSS, -1R
- `test_short_win_outcome` — SHORT TP hit
- `test_short_loss_outcome` — SHORT SL hit
- `test_review_timeout` — no TP/SL hit within review window
- `test_conviction_filter` — signals below min_conviction excluded
- `test_compute_stats_empty` — no signals → safe defaults
- `test_compute_stats_mixed` — correct WR, EV/trade, profit_r aggregation

### A2: Historical Outcome Resolution (~6 tests)
**File:** `test_signal_log.py` (extend existing)
**Why:** Candle-walk logic with simultaneous TP/SL is the trickiest code path.

- `test_historical_long_tp_hit` — candle high crosses TP
- `test_historical_short_sl_hit` — candle high crosses SL for SHORT
- `test_historical_both_hit_bullish_candle` — LONG + both hit + bullish → LOSS (SL first)
- `test_historical_both_hit_bearish_candle` — LONG + both hit + bearish → WIN (TP first)
- `test_historical_review_no_candles` — no candles after signal → REVIEW if expired
- `test_historical_skips_no_price_data` — missing candle data → skip gracefully

### A3: TradeAnalyzer Integration (~5 tests)
**File:** `test_analyzer.py`
**Why:** Recommendation engine drives config changes. Bad recs = bad trading.

- `test_bucket_function` — conviction 80→"75+", 70→"65-74", 60→"55-64"
- `test_coin_stats_calculation` — WR, R-profit, avg hold hours from mock positions
- `test_streak_analysis` — W-W-L-W → longest_win=2, current=1×WIN
- `test_compare_backtest_vs_live_flags_divergence` — >15% gap flagged
- `test_compare_no_overlap` — coin in backtest but not live → no flag

---

## Phase B: Frontend E2E Expansion (Priority 2 — catches integration breaks)

### B1: Data Rendering Smoke Tests (~8 tests)
**File:** `frontend/tests/data-rendering.spec.ts`
**Why:** Confirms API data actually renders. Catches shape mismatches.

- `test_dashboard_status_bar_renders` — market state text visible
- `test_dashboard_active_setups_or_empty` — setup cards OR "No setups" message
- `test_dashboard_active_signals_or_empty` — signal rows OR empty state
- `test_dashboard_btc_card_shows_price` — BTC price number visible
- `test_analytics_best_setups_tab` — click tab → table or empty state renders
- `test_analytics_signal_log_tab` — click tab → signal rows or empty state
- `test_analytics_backtest_tab` — click tab → leaderboard or empty state
- `test_chart_sidebar_loads_signals` — navigate to BTC chart → signal intel panel visible

### B2: Trading Page Tests (~6 tests)
**File:** `frontend/tests/trading.spec.ts`
**Why:** Trading page is newest and most fragile. Config changes affect real behavior.

- `test_trading_page_loads` — `/trading` renders without crash
- `test_portfolio_summary_visible` — balance, equity, exposure shown
- `test_positions_table_or_empty` — positions table OR "No positions" state
- `test_config_panel_loads` — trading config form renders with current values
- `test_pause_button_works` — click pause → "Trading paused" confirmation
- `test_stats_section_renders` — win rate, profit factor, or "No trades yet"

### B3: Error Resilience Tests (~4 tests)
**File:** `frontend/tests/error-states.spec.ts`
**Why:** Backend goes down during development. Frontend should degrade gracefully.

- `test_dashboard_loads_with_backend_down` — page renders (maybe with error banners), doesn't white-screen
- `test_chart_page_no_data_graceful` — chart page with invalid symbol shows error, not crash
- `test_analytics_empty_state` — fresh install with no data → empty states, no JS errors
- `test_trading_empty_state` — no positions/trades → proper zero-state UI

---

## Phase C: Contract Tests (Priority 3 — catches API/frontend drift)

### C1: API Shape Snapshot Tests (~6 tests)
**File:** `test_api_contracts.py`
**Why:** Frontend expects specific JSON shapes. Backend refactors can silently break them.

- `test_portfolio_response_shape` — has: balance, unrealized_pnl, total_equity, exposure, mode
- `test_positions_response_shape` — has: data (list), total (int)
- `test_signal_log_stats_shape` — has: coins (list of {symbol, win_rate, profit_r, ...}), overall
- `test_best_setups_response_shape` — has: data (list of {symbol, direction, conviction, entry, tp, sl, ...})
- `test_oracle_response_shape` — has: signal, bias, earnest.voters, macro.details, targets, performance
- `test_titan_response_shape` — has: signal, confidence, trend, momentum, targets, indicators

These tests call the real route handler (with mocked DB/Redis) and assert the response dict has all required keys. They act as a contract — if a key is renamed or removed, the test fails before the frontend breaks.

---

## Execution Priority

```
Now:       Phase A1-A3 (~19 backend tests) — pure logic, fast to write, high value
Next:      Phase B1-B2 (~14 E2E tests) — needs running frontend, catches real breaks
Later:     Phase B3 + C1 (~10 tests) — error resilience + contract safety
```

## Running Tests

```bash
# Backend (in Docker)
docker compose exec backend pytest -v                          # All 230+ tests
docker compose exec backend pytest --cov=app tests/            # With coverage
docker compose exec backend pytest tests/test_signal_log.py -v  # Single file

# Frontend E2E (requires running services)
docker compose up -d
cd frontend && npx playwright test                    # All E2E
cd frontend && npx playwright test tests/trading.spec.ts  # Single file
cd frontend && npx playwright test --ui               # Interactive mode

# TypeScript check
cd frontend && npx tsc --noEmit
```

## When to Run What

| Event | Run |
|-------|-----|
| Changed backend Python | `pytest -v` (full backend suite) |
| Changed frontend component | `tsc --noEmit` + `playwright test` |
| Changed API response shape | `pytest test_api_contracts.py` + `playwright test` |
| Changed trading config/logic | `pytest test_trading.py test_signal_log.py test_optimization_routes.py` |
| Changed strategy (Oracle/Titan) | `pytest test_oracle.py test_titan.py test_analytics_stats.py` |
| Before any deploy/merge | Full backend + E2E + tsc |
| After adding new coin/pair | `pytest test_signal_log.py` (watchlist tests) |
