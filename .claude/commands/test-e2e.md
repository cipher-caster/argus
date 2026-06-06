# /test-e2e — Frontend E2E Tests

**Usage:**
- `/test-e2e` — Run the frontend E2E tests (data rendering smoke tests, trading page tests)

---

## How to Execute This Skill

These tests catch integration breaks where API data fails to render or trading page state diverges from backend.

- Data rendering smoke tests (dashboard, analytics tabs, BTC card, signal intel)
- Trading page tests (config loading, position updates, P&L display)

Run these sequentially from the `frontend/` directory:

1. **Data Rendering Smoke Tests**
   ```bash
   cd frontend && npx playwright test tests/data-rendering.spec.ts -v
   ```
   Coverage:
   - `test_dashboard_status_bar_renders` — market state text visible
   - `test_dashboard_active_setups_or_empty` — setup cards OR "No setups" message
   - `test_analytics_best_setups_tab` — click tab → table or empty state
   - `test_analytics_signal_log_tab` — signal rows or empty state
   - `test_chart_sidebar_loads_signals` — signal intel panel visible

2. **Trading Page Tests**
   ```bash
   cd frontend && npx playwright test tests/trading.spec.ts -v
   ```
   Coverage:
   - `test_trading_page_loads` — `/trading` renders without crash
   - `test_trading_enable_disable_toggle` — toggle trading mode
   - `test_trading_position_list_updates` — positions reflect API state
   - `test_trading_pnl_calculation` — P&L display matches backend
   - `test_trading_config_persistence` — settings survive refresh

## Full Validation

Run all frontend E2E tests:
```bash
cd frontend && npx playwright test tests/data-rendering.spec.ts tests/trading.spec.ts -v
```

Covers frontend data-shape integration and trading page state.
