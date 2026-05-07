---
name: Argus implementation best practices
description: Project-specific rules for any code change in Argus — gate parity, schemas, caching, config precedence, test discipline
type: feedback
originSessionId: e8dc91a7-8713-485f-bd3f-8e7acb71133b
---
Project-specific rules that apply to ANY code change in Argus. Gate parity is the load-bearing one — divergence between backtest and live silently destroys the optimizer's signal.

**1. Backtest gate logic must match live gate logic.**
**Why:** The optimizer's recommendations are only meaningful if backtest and live use the same regime gate, conviction floor, watchlist, and risk gates. A prior incident (audited 2026-05-07) had backtest using Oracle 1D macro bias while live used BTC weekly EMA50 — every "validated" param change was calibrated against a filter that wasn't running. Fixed by centralizing on `compute_btc_weekly_regime()` in `backend/app/jobs/signal_log.py` and `REGIME_CACHE_KEY = "market:regime"`.
**How to apply:** If you change a gate (regime, conviction, watchlist, ATR mult, expiry) in one place, change it in BOTH `backtest_engine.py` AND the live path (`signal_log.py`, `worker.py`, `orchestrator.py`). Search for the gate symbol across both before merging.

**2. `DEFAULT_TRADING_CONFIG` is fallback only — Redis `trading:config` overrides at runtime.**
**Why:** Changing the default in `orchestrator.py` will NOT affect a running system. Two prior config changes (risk, conviction) failed to take effect because the live Redis config was still the old value.
**How to apply:** After any `DEFAULT_TRADING_CONFIG` change, the user must `POST /api/trading/config` or flush Redis `trading:config` for the change to apply. State this explicitly in the PR/report.

**3. Always check existing tests before writing code.**
**Why:** Tests in `backend/tests/` (e.g., `test_analyzer.py`, `test_trading.py`, `test_rejected_signals.py`) often pin the exact behavior you're about to change. Updating them as part of the change keeps CI green and documents the migration.
**How to apply:** Before editing a module, `ls backend/tests/ | grep <module>` and read the matching test file. Update fixtures in the same PR.

**4. Raise from the `exceptions.py` hierarchy at API boundaries.**
**Why:** `DataProviderError` → 503, `ValidationError` → 400, `CacheError`/`CalculationError` → 500. Bare exceptions become 500s with no diagnostic value.
**How to apply:** Any new code path that calls Binance/OKX/Redis/pandas-ta should raise from this hierarchy. Validate at FastAPI route boundaries with Pydantic v2.

**5. Cache through `services/market_data.py` keys.**
**Why:** Cache TTLs are coordinated there (30–180s for market data, 1hr for regime). Ad-hoc Redis writes from other modules cause cache stampedes and stale reads.
**How to apply:** New cached values should add a key constant + TTL in one place. Workers and routes should both reference the constant.

**6. Worker jobs run on schedules — don't assume they ran.**
**Why:** `execute_signals` every 10 min, `manage_positions` every 5 min, `sync_trading_balance` every 10 min, `signal_log` jobs at 4H candle close. A bug in a job can leave state stale for an hour.
**How to apply:** When debugging "why is X not updated?", check the job schedule and last-run time before assuming a code bug. Tail `docker compose logs -f worker`.

**7. Frontend TanStack Query staleTime is 60–300s.**
**Why:** UI reads will lag behind backend writes by up to 5 min. "Backend changed but UI didn't" is usually cache, not a bug.
**How to apply:** When a backend change is deployed, force a hard refresh or shorten the relevant `staleTime` if the change must be visible immediately.

**8. Always run `/backtest` before deploying strategy/risk changes.**
**Why:** Already a hard rule (see `feedback_backtest_before_deploy.md`). Live edge is too small to risk on un-validated changes.
**How to apply:** No strategy/risk param change ships without a backtest delta showing non-negative EV vs current production config.
