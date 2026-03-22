# /test-phase-b — Frontend E2E Expansion (B1–B2)

**Usage:**
- `/test-phase-b` — Run all Phase B tests (data rendering smoke tests, trading page tests)

---

## How to Execute This Skill

> **⚠️ Implementation Guide** — These test files do not exist yet. This skill guides you through writing and running them. Implement the tests first, then use the commands below to verify.

Phase B tests catch integration breaks where API data fails to render or trading page state diverges from backend.

- **B1:** Data rendering smoke tests (dashboard, analytics tabs, BTC card, signal intel)
- **B2:** Trading page tests (config loading, position updates, P&L display)

Implement and run these sequentially from `frontend/` directory:

1. **B1: Data Rendering Smoke Tests**
   ```bash
   cd frontend && npx playwright test tests/data-rendering.spec.ts -v
   ```
   Coverage:
   - `test_dashboard_status_bar_renders` — market state text visible
   - `test_dashboard_active_setups_or_empty` — setup cards OR "No setups" message
   - `test_analytics_best_setups_tab` — click tab → table or empty state
   - `test_analytics_signal_log_tab` — signal rows or empty state
   - `test_chart_sidebar_loads_signals` — signal intel panel visible

2. **B2: Trading Page Tests**
   ```bash
   cd frontend && npx playwright test tests/trading.spec.ts -v
   ```
   Coverage:
   - `test_trading_page_loads` — `/trading` renders without crash
   - `test_trading_enable_disable_toggle` — toggle trading mode
   - `test_trading_position_list_updates` — positions reflect API state
   - `test_trading_pnl_calculation` — P&L display matches backend
   - `test_trading_config_persistence` — settings survive refresh

## Full Phase B Validation

Run all Phase B tests:
```bash
cd frontend && npx playwright test tests/data-rendering.spec.ts tests/trading.spec.ts -v
```

**Target:** 14 new tests (8 + 6) covering frontend integration and trading page fragility.

**Why:** Frontend E2E only covers navigation. No data shape validation, no error states, no trading page tests.
