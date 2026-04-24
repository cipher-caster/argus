# Changelog

All notable changes to this project will be documented in this file.

## [v1.1.2] - 2026-04-24 — Backend Dead Code Removal & Bug Fixes

### Fixed

- **`_get_btc_oracle_signal()` always returned `""`** — was reading `item["signal"]` from the Oracle screener cache, but the screener stores `item["opportunity"]` (values: `LONG`/`SHORT`/`NONE`). BTC oracle signal context was silently missing from every signal log entry. Fixed and tests updated to use real screener schema.
- **`SignalLogConfig` default watchlist out of sync** — schema default had 10 coins; `DEFAULT_WATCHLIST` in `signal_log.py` had 13 (STRK, POL, AVAX added 2026-04-20 were missing). Cold-start Redis served the wrong watchlist to the UI config endpoint.
- **`TitanRadarItem` silently dropped `mss_type`/`sweep_type`** — `analytics.py` computed and set these fields but `TitanRadarItem` had no matching schema fields; Pydantic discarded them. Both fields added as `Optional[str]`.

### Changed

- **`DEFAULT_COINS` in backtest engine synced to live watchlist** — APT (removed 2026-04-20, 39.2% WR) replaced with STRK, POL, AVAX. Backtest-vs-live comparison was biased while APT remained in backtest defaults.

### Removed

- **`schemas/validation.py` deleted** — 82-line file (`SymbolValidator`, `TimeframeValidator`, eight request models) that was never imported anywhere in the application.
- **`log_contrarian_signals` removed** — 98-line job permanently guarded by `COUNTER_REGIME_ENABLED = False` (13.6% WR, disabled after data review). Cron registration and `COUNTER_REGIME_ENABLED` flag also removed. Dead counter-signal branch in `log_best_setups` cleaned up.
- **`SYMBOL_OVERRIDES = {}` and dead override branches** — empty dict with live conditional checks in `calculate_risk_levels`. Overrides were removed 2026-03-27; the lookup code was never reached.
- **`RiskManager.check_max_positions` stub** — method body was `return True, ""`. Max-position logic already handled in `check_all`; this stub was never called.
- **`MarketIndicators` Pydantic model** — defined in `market_indicators.py` but never instantiated; route returns a plain dict.
- **Dead imports** — `sqlalchemy.orm.sessionmaker` (storage.py), `datetime` (data_provider.py), duplicate `import os` (worker.py).
- **`adx` parameter from `TitanStrategy._calculate_risk_levels`** — never passed by caller, never read in body.

### Fixed (hygiene)

- `print()` calls in `market_indicators.py` and `backtest_engine.py` replaced with `logger`.

---

## [v1.1.1] - 2026-04-20 — Signal Quality & Conviction Calibration

### Fixed

- **Backtest conviction inflation** — `backtest_engine.py` hardcoded `regime_bonus = 20` for all backtest signals regardless of direction, inflating conviction scores by +20 vs equivalent live signals. Counter-regime backtest signals (e.g. BEARISH-bias long) were appearing to pass the min_conviction gate in analysis when they would not have fired live. Fix: derive `regime_aligned` from `btc_macro["bias"]` (BTC 1D oracle, already in scope) and delegate to the shared `calculate_conviction()` utility. Backtest and live conviction scores now use identical logic.

### Changed

- **`min_conviction` lowered 60 → 56** — data-driven decision based on 195 resolved live/scanner signals. Titan's most common signal — standard trend continuation (clean trend, no RSI extreme, no SMC event) — always produces `confidence=60` → `conviction=56`. Setting the gate above 56 silently disables the entire standard-trend signal class. Live signals at conviction=56 have **75.7% WR** over 70 resolved trades; raising to 60 produced zero positions for 3 days. Default code config updated in `orchestrator.py` and documented in `trading_utils.py`.

- **APTUSDT removed from watchlist** — 39.2% win rate over 125 signals, worst performer with a meaningful sample. Removed from `DEFAULT_WATCHLIST` in `signal_log.py`, schema defaults in `analytics.py` / `schemas/analytics.py`, routes default, and correlation group in `orchestrator.py`. Live Redis config updated.

- **`block_btc_sell` stub deleted** — flag existed in schema, job defaults, route defaults, tests, frontend type, and UI toggle, but was never read by `signal_log.py` (unwired stub). Removed entirely from all layers to eliminate dead configuration surface.

### Added

- **5 backtest conviction unit tests** (`TestBacktestConviction` in `test_backtest_engine.py`) — verify regime-aligned bonus, misaligned penalty, neutral case, and market-signal stacking against the corrected formula.

---

## [v1.1.0] - 2026-04-11 — Phase 19: Daily Win-Rate Snapshot System

### Added

- **`signal_outcome_snapshot` table** — new PostgreSQL table that stores daily win-rate snapshots sliced by `(snapshot_date, regime, conviction_band, source, coin)`. Both granular slices and "ALL" rollup rows are written each day, enabling trend queries across any filter combination. Schema: `backend/app/schemas/snapshot.py`, migration: `backend/migrate_v0_19_0.py`.
- **`snapshot_signal_outcomes` worker job** — daily cron at **00:05 UTC** that aggregates all resolved `signal_log` rows (WIN/LOSS/REVIEW/REJECTED) into `signal_outcome_snapshot`. Idempotent: skips any date where the grand-total sentinel row already exists. Accepts an optional `snapshot_date` parameter for targeted backfill. Registered in `backend/app/worker.py`.
- **Worker startup snapshot backfill** — on every worker restart, the startup hook checks the last 7 days for missing snapshot dates and calls `snapshot_signal_outcomes()` for each gap. Non-fatal: a backfill failure logs a warning and does not block startup.
- **`regime_at_signal` and `btc_price_at_signal` columns on `signal_log`** — capture the active BTC regime and BTC spot price at the moment each signal is fired (entry-time context). Previously only resolution-time context (`regime_at_resolution`, `btc_price_at_resolution`) was persisted. The snapshot job uses `regime_at_signal` as the primary regime dimension.
- **`GET /api/analytics/signal-outcomes/trend` endpoint** — returns a daily win-rate time-series from `signal_outcome_snapshot`. Query params: `days` (1–365, default 30), `regime`, `conviction_band`, `source`, `coin`. Also returns `regime_breakdown` and `conviction_breakdown` dicts aggregated across the window. Response cached in Redis for 1 hour.
- **`WinRateTrend` chart component** — new Analytics tab ("Win Rate Trend") that renders the daily win-rate time-series as a line chart with regime and conviction breakdown summaries. Loaded lazily via `dynamic()`. Source: `frontend/src/components/analytics/WinRateTrend.tsx`.

---

## [v1.0.0-alpha] - 2026-04-05 — Dashboard Polish & Error Handling

### Added

- **Shared `CardError` component** — consistent `WifiOff` error state used across all dashboard cards; replaces silent nulls and misleading empty states when backend is offline
- **TradingWidget skeleton** — proper loading skeleton while portfolio data is fetching (previously returned null silently)
- **ActiveSignals skeleton rows** — 3 skeleton rows with matching column layout (previously showed plain "Loading..." text)
- **DashboardWatchlist full skeleton** — full row skeletons while tickers load, matching watchlist item count

### Fixed

- **TradingWidget** — no longer disappears when backend is down; shows error card and preserves layout
- **TopMovers** — no longer disappears silently on error
- **BTCCard** — no longer renders with `$0` on fetch failure; shows error card
- **Best Setups / Active Signals** — no longer show misleading "no data" empty states on error

---

## [0.9.9] - 2026-04-05 — Dashboard Layout Redesign

### Changed

- **Dashboard layout restructured** — new row order: Status Bar → Best Setups + BTC + Watchlist → Active Signals + Paper Trading → Top Movers
- **Active Signals and Paper Trading share one row** — Active Signals (60%) left, Paper Trading (40%) right; aligned with the grid columns above
- **Top Movers moved to bottom** — gainers/losers strip is supplementary context, no longer interrupts the main flow
- **Gainers/Losers back to two rows** — each on its own row with up to 10 coins, hidden scrollbar
- **Paper Trading widget** — added tooltip, "Trading →" chevron link, `Pending` label (was `Open`), card style unified with Best Setups (`bg-secondary/30 border-border/50`)
- **Active Signals** — added column headers (Entry, TP, SL, Conv., Age), left-aligned columns with fixed widths, card style unified
- **Best Setups** — fixed center column spacing with proper flex layout and fixed-width price column; analytics link changed to chevron style
- **Tooltip positioning** — all dashboard tooltips now use `side="bottom" align="start"` (lower-right of trigger)

---

## [0.9.8] - 2026-04-05 — Paper Trading Config & UI Fixes

### Changed

- **Paper trading defaults updated for testing** — `initial_capital`: $200 → $1,000, `max_position_size_pct`: 7% → 3%, `max_drawdown_pct`: 12% → 15% (floor at $850)
- **Default config aligned with live Redis config** — `orchestrator.py` fallback defaults now match production settings; Redis flush no longer reverts to aggressive values

### Fixed

- **Max Leverage missing from UI** — `max_leverage` field added to Risk Settings panel with hint "Notional size cap per trade (× balance)"; also added to `TradingConfig` TypeScript interface

---

## [0.9.7] - 2026-04-05 — Scanner Signal Scoping

### Changed

- **Scanner logs all top-50 coins for scouting** — `log_best_setups` no longer filters to watchlist. Non-watchlist signals appear in the Signal Log Scanner tab with full outcome tracking (WIN/LOSS/REVIEW) but are never paper traded.
- **Trading gated at `execute_signals`** — Only watchlist coins are passed to the orchestrator. Non-watchlist scanner signals are logged and resolved but skipped for position creation.

### Fixed

- **Non-watchlist coins were being paper traded via scanner** — `log_best_setups` read from the `analytics:best-setups` cache which scans top 50 Binance coins, not the watchlist. This caused coins like SOL, ADA, LINK etc. to appear in paper trading positions.

### Data

- **Cleaned 101 non-watchlist scanner signals** (34 coins) and 3 linked positions / 5 trade events from the database.

---

## [0.9.6] - 2026-04-04 — Pre-Production Hardening

### Added

- **Batch race condition fix** — `process_signal()` now accepts `batch_positions` parameter; positions created in the same scan cycle are visible to risk gates (orchestrator.py, worker.py)
- **ADX(14) indicator added to Titan strategy** — previously referenced but never calculated (titan.py)
- **ADX value logged with each signal fired** — observe-only for 7-day observation period (signal_log.py)
- **3 new batch race condition tests** — in test_trading.py (392 total tests passing)
- **Pre-production audit report** — `docs/market-reports/2026-04-04-pre-prod-audit.md`
- **Trading data backup before reset** — `docs/trading/position_backup_2026-04-04.csv`, `trade_event_backup_2026-04-04.csv`, `signal_log_backup_2026-04-04.csv`

### Changed

- **Risk parameters tightened for $200 paper trading observation:**
  - initial_capital: 1000 → 200
  - max_position_size_pct: 10% → 3% ($6 risk per trade)
  - max_leverage: 3.0 → 2.0
  - max_total_exposure_pct: 300% → 200%
  - max_drawdown_pct: 15% → 12% (floor at $176)
  - order_expiry_hours: 24 → 16
- **Paper trading balance reset** — to $200 for 7-day observation period (Apr 4–11)

### Fixed

- **Batch signal processing race condition** — multiple signals in same scan cycle could bypass exposure and concurrency gates because each `process_signal()` opened independent DB sessions

---

## [0.9.16] - 2026-04-02 — Regime Lag Analysis & Monitoring

### Added

- **`/regime-check` slash command** — Diagnostic tool that pulls current regime, 7-day trade performance, and checks for timeframe disagreement between weekly EMA50 and 4H EMA200. Flags regime lag (3+ consecutive losses in same direction) and repeat exposure (pending orders matching losing direction).

### Documented

- **Regime lag incident** — Logged in `docs/trading/knowledge.md`. Weekly EMA50 stayed BEAR while BTC pumped on 4H → 9/10 shorts stopped out (-$688). Root cause: hard regime gate + lagging weekly indicator.
- **Option D planned** — Multi-timeframe confirmation (require 4H EMA200 + weekly EMA50 agreement before firing). To be implemented after backtesting.

---

## [0.9.15] - 2026-03-31 — Signal Resolution Bug Fix

### Fixed

- **Signal resolution used ticker price instead of TP/SL level** — When resolving WIN/LOSS outcomes via fast-path (current ticker price), the code was using the current market price as `resolved_price` instead of the actual TP/SL target. This caused two issues:
  1. `signal_log.resolved_price` didn't match `tp` for SHORT signals where ticker was slightly below TP (e.g., 1.17 vs TP 1.170254)
  2. Linked positions were closed at ticker price instead of TP level, resulting in incorrect PnL calculations
- **Positions linked to WIN signals fixed** — 10 positions across scanner/live sources had their `actual_exit`, `pnl_usd`, `pnl_pct`, and `outcome` corrected to reflect closing at the TP level instead of the (lower) ticker price. This increased reported PnL by ~$1,000 total.

### Code Changes

- `signal_log.py` fast-path resolution: now sets `resolved_price = sig.tp` (or `sig.sl` for LOSS) instead of current ticker price
- `signal_log.py` historical resolution: uses `sig.tp`/`sig.sl` directly for exit price when closing linked positions

---

## [0.9.14] - 2026-03-31 — Phase 21A Complete: OKX Integration

### Added

- **Chart provider decoupling** — Chart page now has a local Binance/OKX toggle in the chart header. Switching to OKX for chart viewing no longer calls `PUT /api/provider` or affects the paper trading engine. Provider resets to Binance on navigation.
- **Chart-global provider sync** — Chart page now syncs with global provider from navbar. When you switch provider in navbar, the chart automatically uses the selected provider for fetching candles.
- **`GET /api/analytics/provider-comparison`** — New endpoint comparing signal performance by exchange. Returns win rate, total signals, wins/losses, avg R-profit, and top 5 coins per provider. Only WIN/LOSS outcomes included (REVIEW/REJECTED/OPEN excluded). Surfaced as a summary banner in BacktestPerformance above the coin table.
- **`TRADING_PROVIDER` config** — `trading_provider` field added to `DEFAULT_TRADING_CONFIG` (default: `"binance"`). Validates to `"binance"` or `"okx"` at the API boundary. Orchestrator uses the configured provider when opening new positions. Toggle added to trading config UI.
- **Daily OKX backfill cron** — `backfill_okx_candles` worker job runs at 02:00 UTC daily, backfilling 7 days of OHLCV data across all 4 timeframes (15m/1h/4h/1d) for all watchlist symbols. Uses retry helper with graceful error handling.

### Fixed

- **OKX past candles pagination** — Fixed import error in `/api/ohlcv-providers` endpoint. Pagination with `end_timestamp` now correctly carries provider through infinite query, allowing users to scroll back in time on OKX charts.

---

## [0.9.13] - 2026-03-30 — Phase 18 Complete: Learning Data Model

### Fixed

- **`market_state_at_close` in manual close** — `manual_close()` in `trading/orchestrator.py` was setting positions to CLOSED without capturing the current market regime. Now fetches regime from Redis (`analytics:signal-summary` → `market:regime` fallback), matching the pattern already used by the automated `check_open_positions()` path. Manually-closed trades will now correctly show regime context in analytics.

---

## [0.9.12] - 2026-03-30 — Signal Log Config, 4H Screener Fix & ActiveSignals Widget

### Fixed

- **4H Oracle cache key** — `signal_log.py` was reading screener results from `analytics:screener:1h:*` keys instead of `analytics:screener:4h:*`. The 4H candle-close scanner was therefore running Titan against 1H screener data, silently producing mismatched signals. Cache key corrected to `analytics:screener:4h:{symbol}`.

### Added

- **Configurable signal log settings (backend)** — `signal_log.py:_get_config()` now reads live config from Redis key `signal_log:config` instead of using a hard-coded dict. Two new REST endpoints in `routes/analytics.py`:
  - `GET /api/analytics/signal-log/config` — returns current config (regime filter, conviction threshold, max signals, etc.)
  - `PUT /api/analytics/signal-log/config` — updates config fields; changes take effect on the next worker cycle without a restart.
- **Signal Log settings UI** — gear icon in the Signal Log tab header opens an inline settings panel. Users can adjust conviction threshold and regime filter mode directly from the analytics page without touching Redis or the API manually.
- **ActiveSignals dashboard widget** — `ActiveSignals` component wired into `frontend/src/app/page.tsx`. Displays currently open live signals from the signal log (source: `live`) on the main dashboard, giving at-a-glance visibility of active trade setups alongside the existing BestSetups and DashboardWatchlist widgets.

---

## [0.9.11] - 2026-03-28 — Outcome Resolution Audit & Hardening

### Fixed

- **Position outcome no longer copies signal outcome** — Historical resolution (`signal_log.py:686`) previously copied the signal's `WIN`/`LOSS` directly to the linked position, ignoring actual PnL. Position outcome is now always derived from `pnl_usd >= 0`, consistent with the fast-path. This was causing 4 positions to be labeled `WIN` despite negative PnL.
- **Unified fee calculation** — Fast-path resolution used `price * quantity * 0.001` for fees while historical used `quote_amount * 0.001`. Both paths now use `quote_amount * FEE_PCT` consistently. Also fixed `pnl_pct` to subtract fee from numerator (`pnl_usd / quote_amount * 100`).
- **Orchestrator uses 5-min tiebreaker** — When both TP and SL are hit in the same 4H candle, the orchestrator previously guessed based on candle direction (bullish=SL first, bearish=TP first). Now imports `_resolve_tiebreaker_5m` from `signal_log.py` to walk 5-min candles and determine which level was hit first, matching the signal log resolution logic.
- **Manual close event type** — `manual_close()` always logged `SL_HIT` even for profitable closes. Now logs `TP_HIT` or `SL_HIT` based on the actual outcome.
- **Pending order price check** — `check_pending_fills()` now checks if price has reached the intended entry before filling. LONG fills only when `current_price <= intended_entry`; SHORT fills only when `current_price >= intended_entry`. Previously filled at any price regardless of distance from limit.
- **Order expiry default** — `check_pending_fills` fallback for missing `order_expiry_hours` was 8 hours instead of 24 (the `DEFAULT_TRADING_CONFIG` value). Aligned to 24 hours.

### Data

- **Historical data fix script** — `scripts/fix_historical_data.py` created to re-resolve all CLOSED position outcomes and PnL using the corrected consistent fee formula. Fixed 4 outcome flips (WIN→LOSS) and 5 PnL recalculations. Run with `--dry-run` to preview.
- **Validation script** — `scripts/validate_outcomes.py` confirms all position outcomes match their PnL (0 mismatches after fix).

---

## [0.9.10] - 2026-03-28 — Signal Resolution & Counter-Trend Assessment

### Fixed

- **Clock-drift sensitive candle fetching** — `get_candles_df` now uses UTC epoch (`time.time()`) for freshness checks instead of local system time. This prevents the worker from skipping data updates when the container clock drifts (e.g. 16-hour drift previously caused stale data to be marked as "fresh").
- **Resolution Lag** — OPEN signals now undergo a "Fast-path" resolution check against live ticker prices every 30 minutes. Previously, signals only resolved on 4H candle closes, causing significant delays in assessing trade performance.
- **Symbol Normalization** — Resolution engine now handles both slash and no-slash symbol formats (`BTC/USDT` vs `BTCUSDT`) seamlessly when mapping exchange ticker data.
- **Regime at Resolution Data** — Fixed "no data" bug by adding `get_oracle_signal_summary` to the worker's cache-warming job. This ensures market state context is available when signals resolve. Added a broad BTC-regime fallback for maximum reliability.
- **Paper Trade Context** — Applied the market-state resolution fix to the paper trading orchestrator. Closed positions will now correctly display the "Market State (Close)" in the Trading History.
- **Missed Entry Logic** — Fixed "teleporting trades" bug where a PENDING position was marked as WIN/LOSS if the signal resolved before entry was hit. These positions are now correctly marked as `CANCELLED` (Missed Entry).

### Added

- **Automated Contrarian Logging** — New `log_contrarian_signals` background job scans the top 50 symbols for mean-reversion opportunities (3x ATR extension from EMA200). These are now automatically logged to the Signal Log (source: `counter`) for performance tracking.
- **Counter-regime Assessment** — The "Counter" tab in Signal Log is now actively populated and assessed, providing near real-time WIN/LOSS data for overextended setups.

## [0.9.9] - 2026-03-28 — Backend Audit & Hardening


### Fixed

- **Silent regime detection failure** — `except Exception: pass` on BTC weekly EMA50 computation in `best-setups` endpoint now logs a warning instead of swallowing the error silently.
- **Raw error leaks in API responses** — 20+ endpoints were returning raw `str(e)` in HTTP 500/503 detail fields. All sanitised to generic messages; full errors logged server-side only.
- **Wrong status code** — generic exceptions in `indicators/calculate` were mapped to 400 (Bad Request); corrected to 500.
- **`apply_experiment` partial-apply risk** — multi-step Redis + DB config update now wrapped in try/except with Redis rollback on failure; previously a mid-flight failure left signal_log config and trading config out of sync.
- **Orchestrator commit failures** — `check_pending_fills`, `check_open_positions`, and `check_circuit_breaker` now catch session commit exceptions, call rollback, and log errors; positions can no longer get permanently stuck in OPEN state on a DB error.
- **N+1 candle inserts** — `session.merge()` loop in `market_data.py` replaced with a single bulk `pg_insert().on_conflict_do_update()` statement.
- **Entry tolerance gate removed** — gate was rejecting valid PENDING positions when price temporarily drifted before the `execute_signals` job ran. LIMIT signals wait for their intended entry via `check_pending_fills` anyway. Removed entirely along with `entry_tolerance_pct` config key.

### Added

- **DB connection pool config** — `create_async_engine` now sets `pool_size=10`, `max_overflow=20`, `pool_recycle=3600`, `pool_pre_ping=True`; previously used SQLAlchemy defaults (pool_size=5).
- **Real health check** — `GET /health` now pings Redis and verifies DB engine; returns 503 with `"degraded"` status if either is unavailable instead of always returning 200.
- **Regime Redis cache** — BTC weekly EMA50 regime cached under `market:regime` with 1hr TTL, shared between `analytics.py` and `signal_log.py`; previously recomputed on every call.
- **Dashboard indicators cache** — `GET /api/indicators/market/dashboard` now caches results in Redis for 300s; previously recomputed on every dashboard load.
- **Worker retry helper** — lightweight `_retry()` async helper (no new deps) wraps exchange ticker fetches and HTTP calls in `worker.py` with 3 attempts and 2s linear delay.
- **Input validation on analytics endpoints** — `timeframe` parameter now validated with regex pattern on `screener`, `contrarian-radar`, `best-setups`, and `titan-radar` endpoints; invalid values return 422.
- **Bounds validation on `TradingConfigUpdate`** — Pydantic `Field` constraints added to all numeric config fields (`initial_capital gt=0`, `max_drawdown_pct le=100`, etc.).
- **CORS whitelist** — `allow_methods` and `allow_headers` tightened from `["*"]` to explicit whitelists.
- **Shared utilities** — `app/utils/trading_utils.py` with `calculate_conviction()` replacing 3 duplicated implementations; `app/constants.py` with `TIMEFRAME_MS` replacing 2 duplicated dicts.

### Tests

- +45 new test cases; **366 backend tests passing, 0 failures** (up from 321 at v0.9.8).
- New test files: `test_trading_utils.py`, `test_constants.py`.
- New test classes covering: regime cache hit/miss, dashboard cache, error sanitisation, timeframe validation, orchestrator commit failures, bulk candle upsert, worker retry, trading config bounds, apply_experiment rollback.

---

## [0.9.8] - 2026-03-27 — Override Bug Fix + Test Suite Repairs

### Fixed

- **SYMBOL_OVERRIDES lookup bug** — backtest engine was calling `SYMBOL_OVERRIDES.get(f"{symbol}USDT", {})` but `symbol` was already in `"BTC/USDT"` format, producing keys like `"BTC/USDTUSDT"` that never matched. Per-symbol overrides (BTC TP=4.0x, ETH TP=4.0x) were silently never applied since they were added. Fix: use `SYMBOL_OVERRIDES.get(symbol, {})`.
- **Per-symbol TP overrides removed** — once the lookup bug was fixed and overrides were actually applied, BTC performance degraded (50.6% → 34.3% WR with TP=4.0x). All TP/SL overrides removed. `SYMBOL_OVERRIDES` is now `{}`. Universal TP=2.0x ATR confirmed optimal.
- **`RiskManager.calculate_position_size`** — fixed risk-based position sizing: max notional cap is now correctly applied as `balance × max_position_size_pct`; leverage cap enforced. Previously generated oversized positions on tight stops.
- **Orchestrator tiebreaker** — same-candle TP/SL hit logic had inverted WIN/LOSS assignment. Fixed.
- **LIMIT signal detection in `process_signal`** — LIMIT signals were not being detected and routed correctly; now handled.
- **Event loop pollution in tests** — `_get_prices` patched in test teardown to prevent async loop contamination across `test_trading.py`.

### Changed

- **`run_signal_backtest.py` defaults** — `tp_mult` default changed from `0.0` to `2.0`; `--fix-optimal` flag no longer forces adaptive TP.
- **`SYMBOL_OVERRIDES` cleared** — all per-symbol TP/SL overrides removed from `TitanStrategy` and backtest engine after override bug was fixed and overrides proved harmful.
- **Test suite: 7 pre-existing failures resolved** — `test_trading.py` now passes 53/53 tests (0 failures). Total backend test count: 321 passing.

### Docs

- **Post-implementation audit** — appended to `docs/market-reports/2026-03-27-backtest-report.md` documenting the override lookup bug discovery and validated final config (TP=2.0x, no overrides, 50.61% WR, +162.7R, 12 REVIEW signals).

---

## [0.9.7] - 2026-03-27 — Fixed TP Default (Backtest-Driven)

### Changed

- **Default TP switched from adaptive to fixed 2.0x** — backtest sweep across 886 signals showed fixed 2.0x ATR dominates adaptive TP: +2.6% WR (50.9% vs 48.3%), +0.019R EV/trade, 50% fewer REVIEW signals. The adaptive 3x SUPER TREND bonus hurt most alts (ATOM 11%, BNB 0%, DOGE 15% WR in that state).
- **`BacktestConfig` defaults** — `tp_mult=2.0`, `tp_adaptive=False`. The `tp_adaptive` field is kept for backward compat but no longer the default.
- **`TitanStrategy._calculate_risk_levels`** — removed ADX-based adaptive TP logic. Now uses fixed `default_tp_mult=2.0`. Note: per-symbol overrides (BTC SL=1.75x/TP=4.0x, ETH TP=4.0x) existed in code but were never applied due to a key-format lookup bug (see v0.9.8). Overrides have since been removed entirely.
- **All sweep scripts** (`run_signal_backtest.py`, `okx_backtest.py`, `optimize_trading.py`) — default configs updated to fixed 2.0x.
- **Trailing stops tested and rejected** — both trail-at-TP and breakeven-at-50% were catastrophically worse than fixed TP. No changes made.

### Why

Backtest report `docs/market-reports/2026-03-27-backtest-report.md` ran 6 experiments. Key findings:
- Fixed TP=2.0x: 50.9% WR, +0.185R EV (best overall)
- Adaptive TP: 48.3% WR, +0.166R EV (current prod)
- TP=4.0x: 31.6% WR, +0.145R EV (clearly negative for alts)
- The 3x SUPER TREND bonus is a trap for 9/11 coins — only BTC/ETH thrive in it (already handled by per-symbol overrides)

---

## [0.9.6] - 2026-03-27 — Backend Codebase Assessment Fixes

### Fixed

- **Provider leak** — `get_provider()` factory previously created a new CCXT exchange instance (and called `load_markets()`) on every OHLCV request from `services/market_data.py`, `routes/analytics.py`, and `routes/strategy.py`. Under load this hammered Binance's API and left orphan connections. The backend now uses a single shared provider singleton registered at startup via `set_shared_provider()`.
- **Hardcoded provider tag** — candles fetched via OKX were saved to the DB with `provider="binance"`, causing an infinite cache-miss loop when the active provider was OKX. Both `market_data.py` and `strategy.py` now use `provider.name` dynamically.
- **Tiebreaker using closed provider** — `_resolve_tiebreaker_5m()` in `signal_log.py` was called with `shared_provider` after it had already been closed in the `finally` block above. The tiebreaker was silently falling back to LOSS on every same-candle TP+SL hit. Fixed by making `provider` optional (default `None`) — `get_candles_df` manages its own provider lifecycle when no provider is passed.
- **Singleton not closed by routes** — `routes/analytics.py` and `services/market_data.py` now use `owns_provider()` to guard `close()` calls: only close a provider if the caller created it (worker/test context); never close the app-lifetime singleton.
- **Oracle backtest timestamp type error** — `exit_time` assignment in `oracle.py` called `.timestamp()` unconditionally, which raises `AttributeError` when the column contains raw integer timestamps (API path) instead of `pd.Timestamp` objects (DB path). Now uses the same `isinstance(ts, pd.Timestamp)` guard as `calculator.py`.
- **Silent exception swallow** — bare `except Exception: pass` in `market_data.py` symbol-filter path now logs a warning instead of discarding the error silently.

### Changed

- **`providers/__init__.py`** — `get_provider()` now returns the shared singleton when registered (backend process) and falls back to creating a new instance (worker process, tests). Adds `set_shared_provider()` and `owns_provider()` to the public API.
- **`DataProvider` ABC** — `close()` and `get_all_tickers()` are now declared as `@abstractmethod`, enforcing the contract on all subclasses.
- **Dead code removed** — `_passes_market_gate()` in `signal_log.py` (all three branches returned `True`; the function was never called) has been deleted along with its three unit tests.
- **`test_fvg.py` cleanup** — removed unused `importlib.metadata`, `os` imports and the brittle `sys.path.append("/app")` Docker-path hack.

---

## [0.9.5] - 2026-03-27 — Market-Fill Entry + Position Sizing Fix

### Fixed

- **Market-fill all positions immediately** — all signals now fill at current market price on entry; `intended_entry` is preserved for reference. Previously, all Titan signals were `SELL_LIMIT`/`BUY_LIMIT` and stayed PENDING indefinitely waiting for price to retrace to the intended level, which rarely happened.
- **Position sizing** — `max_position_size_pct` now correctly caps the **notional** position size (balance × pct). Previously it was used as a risk-per-trade amount, generating oversized positions (e.g. 3× balance per position on tight stops).

### Added

- **Entry tolerance gate** — new `entry_tolerance_pct` config param (default 1%). Signals are skipped if the current price has drifted more than this % past the intended entry in the trade direction. Prevents taking trades where the R:R is already degraded (e.g. shorting after price has already dropped 2% below the intended entry level). Logged as a risk rejection with drift % reason.

### Changed

- `DEFAULT_TRADING_CONFIG` gains `entry_tolerance_pct: 1.0`

---

## [0.9.4] - 2026-03-26 — Counter-Regime Signal Tracking

### Added

- **Counter-regime signal tracking** — scanner job now logs regime-misaligned signals to `signal_log` with `source='counter'` (conviction ≥ 50). These are tracked for performance observation only; they are never paper traded. `execute_signals` filters on `source IN ('live', 'scanner')`, so counter signals are completely safe from execution.
- **Signal Log UI: "Counter" tab** — new source filter tab in the Signal Log analytics panel to browse counter-regime setups and observe their outcomes over time.

### Changed

- **Best Setups: regime filter removed from UI** — the Best Setups component now displays all signals regardless of regime alignment (both regime-aligned and counter-regime setups). Regime filtering is enforced at the scanner job logging layer, not the UI.
- **Scanner conviction threshold: 60 → 50** — `log_best_setups` job now logs signals with conviction ≥ 50 (down from 60), aligning with the SELL_LIMIT signal scoring range observed in BEAR regime. Both `source='scanner'` and `source='counter'` signals are logged at this threshold.

---

## [0.9.3] - 2026-03-22 — 5min Candle Tiebreaker for Signal Resolution

### Fixed

- **Same-candle TP+SL resolution accuracy** — when both TP and SL are hit within the same 4H candle, the old logic used a candle-direction heuristic (bullish/bearish close) to guess which was hit first. This was unreliable and inconsistent with the backtest engine (which assumed conservative LOSS). Now both live resolution and backtest fetch **5min candles** for the 4H window and walk them chronologically to determine the exact TP/SL ordering.
- **Live vs backtest consistency** — the live resolver and backtest engine previously used different tiebreaker logic (heuristic vs conservative). Both now use the same 5min candle walk approach, eliminating discrepancies between backtest results and live signal outcomes.
- **`resolved_at` precision** — when a tiebreaker resolves the signal, `resolved_at` is now set to the actual 5min candle timestamp where the level was hit, not the parent 4H candle open time.

### Added

- `_resolve_tiebreaker_5m()` in `signal_log.py` — fetches 5min candles via `get_candles_df` for the 4H window, walks them to find which level hit first. Falls back to conservative LOSS if 5min data is unavailable.
- `resolve_outcome_with_tiebreaker()` + `_tiebreaker_5m_from_db()` in `backtest_engine.py` — async tiebreaker that loads 5min candles from DB. Falls back to conservative LOSS if data unavailable.
- Original sync `resolve_outcome()` preserved for backward compatibility.

### Tests

- 18 new tests (254 total):
  - `TestTiebreaker5m` (7): TP-first, SL-first, LONG/SHORT directions, no-data fallback, error fallback, both-hit-same-5m-candle skip
  - `TestResolveOutcomesTiebreaker` (2): end-to-end resolution with tiebreaker, no-data fallback
  - `TestTiebreaker5mFromDb` (5): DB-backed tiebreaker scenarios
  - `TestResolveOutcomeWithTiebreaker` (4): normal SL/TP, same-candle tiebreaker, REVIEW
  - `TestResolveOutcomeSync` (2): backward compat

## [0.9.2] - 2026-03-22 — Provider Reuse, Signal-Position Bridge & Fill Rate Fix

### Fixed

- **Worker Binance API rate limiting** — `log_watchlist_setups`, `resolve_outcomes_historical`, and `_recover_missed_scans` were creating a new BinanceProvider per symbol, each hitting `exchangeInfo`. Now share one provider per job run, eliminating 10+ redundant API calls per cycle.
- **Unclosed aiohttp sessions** — shared providers are properly closed via `try/finally`, preventing session leaks that caused `asyncio:Unclosed client session` errors.
- **Signal resolution → position bridge** — when `resolve_outcomes_historical` resolves a signal WIN/LOSS, it now closes the linked position (with PnL calculation and TradeEvent), so resolved trades appear in trade history instead of only in system activity.
- **Server-side pagination** — signal log and trade history endpoints now support pagination (`2292176`).
- **Paper trading fill rate (17% → expected ~80%)** — three root causes addressed:
  - `min_conviction` lowered 60 → 50: all live watchlist signals (conviction 56) were being blocked by risk manager, resulting in zero positions from the best-performing signal source (4W/1L track record).
  - `order_expiry_hours` extended 8 → 24: SELL_LIMIT entries are set above current price (at EMA20/SuperTrend); 8 hours wasn't enough for price to retrace. 24 hours gives a full daily cycle.
  - Market-order instant fill for BUY/SELL signals: high-conviction market signals (conviction 80) now create OPEN positions immediately at current price instead of waiting as PENDING limit orders that may never fill.

### Changed

- **Stopped persisting rejected scanner signals** — `log_best_setups` no longer inserts REJECTED rows for low-conviction scanner signals. These had zero learning value (no outcome tracking, hardcoded rejection reason). Rejection counts still logged to worker stdout. Cleaned up 139 existing rejected rows.

### Docs

- Fixed duplicate "Phase 19" heading in ROADMAP.md (renamed second to Phase 21)

## [0.9.1] - 2026-03-20 — Signal Resolution Fix & System Audit

### Fixed

- **`resolve_outcomes_historical` datetime comparison bug** — `strategy.py:130` converts timestamps to `datetime64`, but the resolution job compared against raw epoch ms integers. Fixed by wrapping `sig.fired_at` with `pd.Timestamp(sig.fired_at, unit="ms")` and converting datetime64 candle timestamps back to epoch ms. Previously stuck signals (ETCUSDT, UUSDT) now resolve correctly.

### Audit (2026-03-20)

Full system audit of Analytics, Trading, and Market pages:

- **Analytics page**: 10/10 endpoints working, 33/33 tests passing, types clean
- **Trading page**: 11/11 endpoints working, 66/66 tests passing, types clean
- **Market page**: 10/10 endpoints working, 10/10 tests passing, types clean
- **Signal log**: 100% win rate on resolved signals (4W/1L), 75% overall
- **Trading**: $963.68 balance (3.6% drawdown), 1 open position (ASTERUSDT SHORT)

### Known Data Model Gaps

- Signal log captures market state at fire time but not at resolution time — can't correlate regime changes to outcomes
- No `regime_at_resolution` or `btc_price_at_resolution` fields
- Rejected signals (low conviction, exposure cap, volatility gate) are logged to stdout but not persisted — can't analyze rejection patterns
- Signal log and positions are disconnected — no analytics query joins signal outcomes to actual position P&L
- Trade events only log TP_HIT/SL_HIT — missing FILLED, PENDING, RISK_REJECTED events
- Backtest tab in analytics is redundant with SignalLog's "Backtest" source filter

## [0.9.0] - 2026-03-19 — Regime Detection & Oracle Deprecation

### Added

- BTC weekly EMA50 regime detection system (`GET /api/strategy/regime`)
- DashboardStatusBar regime modal with actionable advice, aligned setups, execution guidance
- Per-symbol risk overrides in Titan (BTC: SL=1.75x ATR, TP=4.0x ATR)
- Candle-based TP/SL resolution in signal log and paper trading orchestrator
- ETH added to SYMBOL_OVERRIDES (TP=4.0x)
- Analysis scripts: btc_timeframe_analysis, btc_4h_sweep, btc_hodl_vs_trade, btc_titan_deep_dive, eth_full_analysis, regime_detector, btc_eth_db_verify
- Dead code registry (docs/DEAD_CODE.md)

### Changed

- Signal logging uses regime-based direction filtering (BEAR→SHORT only, BULL→LONG only) instead of Oracle market gate
- Best Setups rewritten: Titan-only signals, regime-filtered, no Oracle dependency
- CoinAnalysisModal: regime + Titan (was Oracle + Titan)
- CoinDetailsPanel: Titan-only (was Oracle + Titan)
- Dashboard: Active Setups renamed to Best Setups, shows TP/SL prices
- Dashboard: Active Signals merged into Best Setups
- Analytics: reduced to 3 tabs (Best Setups, Signal Log, Backtest Performance)
- Signal resolution uses candle walk instead of current price check

### Removed

- Oracle from all UI (backend code preserved for future experiments)
- Contrarian Radar from analytics
- OracleScreener from analytics
- Dead /trading page link from dashboard

## [0.8.2] - 2026-03-19

### Added

- **BTC Multi-Timeframe Analysis**: Comprehensive backtest comparing 15m, 1h, 4h, 1d timeframes for BTC across Oracle and Titan strategies.
  - Oracle proven negative for BTC (9-12% WR across all timeframes). Root cause: Earnest voter system generates too many false signals for BTC's strong-trending character.
  - Titan positive on 1h/4h/1d. Best config: SL=1.75x ATR, TP=4.0x ATR on 4H → EV=+0.264R (4x improvement over default +0.061R).
  - Parameter sweep across 6 SL × 7 TP × 5 confidence thresholds on 4H (0.46yr data).
- **ETH Multi-Timeframe Analysis**: Same analysis applied to ETH.
  - Oracle even worse on ETH than BTC (7-21% WR across all timeframes).
  - Titan default settings (SL=1.5x, TP=adaptive) already work well for ETH: EV=+0.167R, 50% WR on 4H.
  - Fixed TP=4.0x gives 3x better EV (+0.494R) with same max drawdown — ETH override added.
  - ETH does need a per-symbol override: `tp_mult=4.0` (fixed, not adaptive). SL stays default 1.5x.
- **Per-Symbol Risk Overrides**: `SYMBOL_OVERRIDES` dict in `titan.py` for coin-specific SL/TP multipliers. BTC defaults to SL=1.75x ATR, TP=4.0x ATR (R:R 2.29). Other coins unchanged (SL=1.5x, TP=adaptive).
- **Analysis Scripts**: `btc_timeframe_analysis.py`, `btc_titan_deep_dive.py`, `btc_4h_sweep.py` in `backend/scripts/` for reproducing results.
- **Strategy Documentation**: BTC analysis section added to `docs/strategies/BACKTEST_RESULTS.md`.

### Changed

- `TitanStrategy.analyze()` now accepts optional `symbol` parameter for per-symbol risk overrides.
- `TitanStrategy._calculate_risk_levels()` applies symbol-specific SL/TP multipliers when available.
- All production call sites updated to pass symbol: `routes/strategy.py`, `routes/analytics.py`, `jobs/signal_log.py`, `trading/backtest_engine.py`, `worker.py`.

## [0.8.1] - 2026-03-19

### Added

- **Test Coverage Expansion (Phase 16a)**: 56 new tests across 3 critical modules (160 → 216 total).
  - `test_signal_log.py` (28 tests): market gate logic, config cache hit/miss, Redis helpers, watchlist/scanner signal insertion, outcome resolution (LONG win/loss, SHORT win, REVIEW timeout).
  - `test_trading_routes.py` (18 tests): all 9 trading API endpoints — portfolio, positions (list/filter/404), history, config (get/put/null), close/close-all, pause, stats with equity curve.
  - `test_indicator_routes.py` (10 tests): indicator list/calculate (DB + provider fallback + 400), market dashboard (with/without data), activity log (limit, event_type filter).

---

## [0.8.0] - 2026-03-19

### Added

- **Paper Trading Engine (Phase 14)**: Full simulation engine for forward-testing signals without real capital.
  - `Position` and `TradeEvent` SQLModel tables tracking the full lifecycle: PENDING → OPEN → CLOSED/EXPIRED.
  - `TradeOrchestrator`: processes signals into positions, checks pending fills, manages TP/SL exits, circuit breaker on drawdown.
  - `RiskManager`: max position size, max concurrent positions, correlated-pair limits, conviction gate.
  - `PortfolioTracker`: real-time P&L, drawdown, position value from live prices.
  - `/trading` frontend page with positions table, trade history, portfolio stats, and config panel.
  - `/portfolio` and `/trade` slash commands for Claude Code.
- **Trading Optimization System (Phase 15)**: Parameter sweep and analysis framework.
  - `BacktestConfig` dataclass and reusable `backtest_engine.py` extracted from CLI script.
  - `OptimizationExperiment` table storing sweep results (23 fields).
  - `optimize_trading.py` CLI with 5 presets: `sl_sweep`, `tp_sweep`, `confidence_sweep`, `gate_sweep`, `full_grid`.
  - `TradeAnalyzer`: compares backtest vs live performance, recommends config changes.
  - API routes: `/api/optimization/experiments`, `/best`, `/apply`; `/api/trading/analysis`, `/recommendations`.
  - `/optimize` slash command for full optimization loop.
  - `docs/trading/knowledge.md` seeded with confirmed findings and dead ends.
- **Signal Consolidation**: Scanner signals (best-setups) now logged to `signal_log` DB with `source='scanner'`.
  - `log_best_setups` worker job reads cached best-setups every 5 min and persists qualifying signals (conviction >= 60).
  - Removed orphaned `TitanSignalsPanel` and `TitanRadar` analytics components.
  - Signal Log UI updated with "Scanner" source filter and violet badge.

### Fixed

- **Scanner signals never became paper trades**: `execute_signals` filtered on `source='live'` only — changed to `source.in_(["live", "scanner"])`.

### Changed

- **Backtest CLI**: Refactored `run_signal_backtest.py` from 555 → ~180 lines — now a thin wrapper over `backtest_engine.py`.

---

## [0.7.0] - 2026-03-18

### Added

- **Signal History Log (Phase 11)**: Complete signal logging system with forward-test track record.
  - Worker scans watchlist at 4H candle closes (6x/day) + startup scan for immediate data.
  - Outcome resolution every 30 min: WIN / LOSS / REVIEW (7-day timeout).
  - Market gate system: block SLEEPING/VOLATILE markets, macro guard, BTC sell filter.
  - Configurable settings UI: watchlist selection, min confidence, review days, gate toggles.
  - 11-coin watchlist selected from 20-coin backtest sweep (BTC, ETH, BNB, TRX, XRP, FET, NEAR, ARB, ATOM, DOGE, APT).
  - `/backtest [COIN]` slash command for running backtests from Claude Code.
- **Backtest Performance Leaderboard (Phase 12)**: New analytics tab with per-coin backtest stats.
  - Sortable table: win rate, R-profit, W/L, long/short split, status badge.
  - Expandable coin rows showing individual signal history (date, direction, entry, TP, SL, outcome, exit price).
- **Chart Signal Intelligence (Phase 13)**: Backtest + signal data integrated into chart deep-dive.
  - `CoinSignalIntel` sidebar panel: compact backtest stats + open signals with TP distance.
  - `CoinAnalysisModal` "Signal Track Record" section: full stats grid, active signals with live TP/SL %, history table.
- **Active Signals Dashboard Widget**: Shows OPEN live signals on the main dashboard.

### Changed

- **Signal Log UX**: Replaced 12 coin filter buttons with dropdown select. Age column now shows full date/time (`Mar 18, 2026 14:30`) instead of relative time (`2d ago`).
- **Worker Schedule**: Signal scanning optimized from every 5 min (288/day) to 4H candle closes (6/day). Resolution changed from hourly to every 30 min.

---

## [0.6.1] - 2026-03-14

### Added

- **Best Setups — Oracle backtest win rate**: Each setup card now shows a color-coded historical win rate badge from the Oracle backtest (`XX% hist.`). Thresholds based on 2:1 RR math (break-even = 33.3%): ≥50% green, 33–49% yellow, <33% red. Shows `— hist.` when `total_trades < 10`.
- **Best Setups — Eliz+Mayne MTF confluence**: Each card shows Titan signal confirmation across 4 timeframes grouped into two analyst lanes:
  - Eliz lane: 4H (entry trigger) + 1D (swing structure)
  - Mayne lane: 12H (higher-TF bias) + 1W (macro/weekly direction)
  - Green badge = confirmed, gray = not aligned. Full 4-TF confluence = highest-conviction swing.
- **Test suite (119 tests)**: Comprehensive backend pytest coverage — Oracle strategy (Earnest voters, signal synthesis, analyze output), Titan strategy (signal enum, confidence range, directional logic, targets), analytics screener robustness, market data, worker jobs, strategy routes.

### Fixed

- **MTF candle limits**: 12H and 1W fetches bumped to 250/200 candles (Titan requires 200+). Was fetching 100, causing `error` returns on those timeframes.
- **Mean reversion boolean output**: Type conversion fix for `is_extended` field.

---

## [0.6.0] - 2026-03-14

### Added

- **Dashboard redesign**: Replaced the 50-coin table with a focused trading layout:
  - `DashboardStatusBar` — single compact row combining Oracle market state, bull/bear %, top long/short signals, Avg RSI, Market Cap, and BTC Dominance. Replaces the old full-width `OracleSignalSummary` bar and separate `MarketPulseStrip`.
  - `ActiveSetups` — shows top 5 `best-setups` results (Oracle + Titan aligned, 4H default). Loads independently with `keepPreviousData`.
  - `BTCCard` — BTC price, 24h change, 7d sparkline, high/low. Shares cache with `DashboardWatchlist` (same `market-tickers` query key — one network request).
  - `DashboardWatchlist` — starred coins with live prices and Oracle score badge. Uses React Query instead of raw `setInterval`.
  - `TopMovers` — gainers and losers on separate rows (5 each), compact chip style.
- **`/markets` page**: Full 50-coin `CoinTable` with sort and pagination, accessible from navbar and dashboard footer link. Frees the dashboard from data overload.
- **`ArgusLogo` component**: Inline SVG React component — geometric eye on indigo rounded square (Argus Panoptes motif). Replaces external PNG. Also set as browser tab favicon via SVG data URI.
- **Chart page — Oracle + Titan signal panel**: `CoinDetailsPanel` now shows Oracle Earnest Score, macro Bias, Titan signal, confidence, and advice text for the current chart symbol. Replaces the redundant "Performance" duplicate card.

### Changed

- **Fonts**: Switched from Inter (`<link>` tag) to **Space Grotesk + DM Mono** via `next/font/google`. Self-hosted, zero layout shift, no external request at runtime.
- **Chart page layout**: Removed the `DrawingToolbar` 48px column — chart is now wider. Layout changed from `grid-cols-[48px_1fr_280px]` to `grid-cols-[1fr_280px]`.
- **ChartHeader cleanup**: Removed dead "Compare symbol" button, dead "Chart Style" button, duplicate Argus brand link, Search icon decoration, and provider badge. Kept: back arrow, symbol+price, timeframe selector, indicators dropdown, refresh, settings.
- **`CoinDetailsPanel`**: Removed redundant "Range" stat (derivable from high/low) and "Performance" card (24h change shown a third time). Replaced with Oracle Score + Titan Signal + Advice section using `useStrategyOracle`.
- **Navbar**: Added "Markets" link. Replaced `<Image>` logo with inline `ArgusLogo` SVG component.
- **MADX removed from dashboard**: Dropped from `MarketPulseStrip` (now `DashboardStatusBar`). Oracle regime bar already communicates trend strength; MADX added no additional decision-making value.

### Fixed

- **Light mode**: All `-400` color variants across dashboard components were invisible in light mode. Fixed with `text-{color}-600 dark:text-{color}-400` pattern across `ActiveSetups`, `DashboardWatchlist`, `DashboardStatusBar`, `CoinTable`, `CoinDetailsPanel`.
- **BTCCard disappearing**: Switched from `useCoins` (separate paginated fetch, returned `null` silently) to `market-tickers` query (shared cache with `DashboardWatchlist`, `keepPreviousData` prevents card vanishing between refreshes).
- **Oracle advice text unreadable in light mode**: `text-amber-200/80` → `text-amber-900 dark:text-amber-200/80`.

---

## [0.5.5] - 2026-03-14

### Removed

- **Market Health**: Redundant with Oracle macro bias (both measure EMA200 bullish/bearish %).
- **Trend Radar**: EMA200 bucket view — same information already surfaced per-coin in Oracle Screener.
- **Structure Scanner**: Monday range breakout/fakeout — niche signal with incomplete logic.
- **Confluence Gauge**: Re-aggregated Oracle Screener scores; replaced by inline `market_state` calculation in `signal-summary` endpoint.
- **Liquidity Map**: PWH/PWL sweep detection — placeholder logic, unreliable signals.

### Changed

- **Analytics page**: Streamlined from 7 tabs to 5 (Oracle Screener, Titan Signals, Titan Scanner, Contrarian Radar, Relative Strength). Removed top ConfluenceGauge banner.
- **Relative Strength**: Restored to analytics sidebar (was previously built but not accessible from UI).
- **signal-summary endpoint**: Now derives `market_state` directly from screener scores instead of calling ConfluenceAggregator. Removes the redundant `calculate_market_health` call.
- **Backend**: Deleted `market_health.py`, `trend_radar.py`, `structure.py`, `confluence.py`, `liquidity.py` from `indicators/`.

## [0.5.4] - 2026-01-31

### Added

- **Unified Market Sentiment Component**: Created reusable `MarketSentimentBar` component for both dashboard and analytics pages.
  - **Component Consolidation**: Merged `OracleSignalSummary` and `ConfluenceGauge` into single 167-line component, eliminating 90+ lines of duplicate code.
  - **Variant Support**: Intelligent switching between Oracle and Confluence data presentation styles.
  - **Consistent Loading States**: Proper `Skeleton` component integration for synchronized loading experience.
- **RSI Range Display**: Added "7d Range: 0 — 100" label below AVG CRYPTO RSI gauge, matching MADX visual style.
- **Timestamp Restoration**: Re-added "Updated" timestamps to all 4 dashboard market indicator cards (MADX, AVG CRYPTO RSI, TOTAL MARKET CAP, BTC DOMINANCE).

### Improved

- **Code Organization**: Dashboard now uses dedicated full-width row for Oracle Intelligence status bar above 4-column grid.
- **Component Reusability**: Both `OracleSignalSummary.tsx` (24 lines) and `ConfluenceGauge.tsx` (27 lines) are now thin wrappers around shared `MarketSentimentBar`.
- **Type Safety**: Fixed TypeScript errors by wrapping React Query `refetch` calls to return `Promise<void>`.

### Changed

- **Layout Adjustment**: Moved Oracle Intelligence from 5-column grid to separate full-width section above 4-card grid for better visual hierarchy.
- **Loading Skeletons**: Updated all market sentiment bars to use consistent h-12 skeleton height (48px).

## [0.5.3] - 2026-01-17

### Added

- **The Trend God (Trend Radar)**: New analytics engine and page (`/analytics`) visualizing the position of assets relative to their 200-Day EMA.
  - **Netflix-Style UI**: Horizontal scrollable rows for each zone (Retesting, Trending, Overextended).
  - **Live Metadata**: Integration with `useCoinMeta` for correct logo display.
- **The Weekly Trap (Structure Scanner)**: New engine identifying Monday Range breakouts, breakdowns, and fakeouts.
  - **Smart Money Detection**: specifically flags "Fakeout Lows" where price sweeps the Monday Low and reclaims it.
- **The Confluence Engine**: Global Market State aggregator.
  - **Sentiment Gauge**: Visualizes market-wide "Earnest Score" consensus (Sleeping vs Tsunami).
- **Documentation**: Added comprehensive guides for all analytics engines in `docs/analytics/`.

### Fixed

- **Missing Icons**: Trend Radar and Structure Scanner now correctly load coin logos from the metadata cache.
- **NameError Fix**: Resolved a crash in the Structure Scanner API endpoint due to a missing schema import.

## [0.5.2] - 2026-01-17

### Added

- **Responsive Dashboard**: Implemented an adaptive grid layout that scales from 1 column (Mobile) to 2 columns (Tablet) and **5 columns (Desktop)**.
- **Oracle Intelligence Integration**: fully integrated the Oracle Intelligence card into the main dashboard grid with a standardized Skeleton loading state.
- **Average Crypto RSI**: Added new indicator card tracking the 14-period RSI average of top 100 coins (Momentum vs Trend).
- **Sparklines**: Added lightweight SVG sparklines to all indicator cards to visualize 7-day trends.

### Improved

- **Indicator Cards Redesign**:
  - **MADX**: Gauge only (Clean trend view)
  - **Average RSI**: Sparkline + Value (Momentum focus)
  - **Market Cap**: Sparkline only (Trend focus)
  - **BTC Dominance**: Gauge only (Clean share view)
- **Data Analysis Widgets**: Limited "Top Gainers", "Top Losers", and "Volume Leaders" lists to the top 3 items (previously 5) for a cleaner, more compact UI.
- **UI Consistency**: Standardized the "Oracle Signal Summary" card to match the visual rhythm and structure of other market indicator cards.

## [0.5.1] - 2026-01-17

### Added

- **Redis Analytics Caching**: Implemented cache-aside pattern for all analytics endpoints with 60s TTL for instant responses.
- **Worker Pre-warming**: New `sync_analytics_cache` job pre-computes analytics for 1h/4h/1d timeframes every 5 minutes.
- **Cache Hit Test**: Added automated test verifying cached responses are returned correctly.

### Improved

- **Frontend UX**: Updated React Query hooks with `gcTime`, `keepPreviousData`, and disabled `refetchOnWindowFocus` for smoother stale-while-revalidate experience.
- **Error Handling**: Analytics data fetching now uses `return_exceptions=True` to prevent single symbol failures from aborting all requests.
- **Logging**: Replaced `print()` statements with proper `logging.warning()` in screener error handling.

### Fixed

- **Operator Precedence Bug**: Fixed incorrect `and/or` chain in market_state calculation that could misclassify market conditions.
- **Hardcoded Rolling Window**: Liquidity sweep detection now calculates the correct bars-per-week based on timeframe (was hardcoded to 168 for hourly).
- **Missing Schema Fields**: Added required fields (`extension_atr`, `price`, `mean`, `target`) to early returns in `mean_reversion.py` to prevent Pydantic validation errors.
- **Test Assertions**: Fixed test checking positional args instead of kwargs for timeframe parameter.

## [0.5.0] - 2026-01-17

### Added

- **Oracle Intelligence Expansion**: Transformed the analytics suite from a hardcoded list to a dynamic screening engine targeting the **Top 100-250 market leaders**.
- **Multi-Timeframe Support**: All analytics views (Screener, Health, etc.) now support **1h, 4h, and 1d** analysis horizons via a global timeframe selector.
- **Oracle Screener**: AI/Quant scoring for the Top 50 high-volume assets.
- **Market Health Dashboard**: Aggregate sentiment and volatility squeeze detection across the Top 100 coins.
- **Liquidity Map**: Detects Swing Failure Patterns (SFP) and Previous Weekly High/Low reclaims.
- **Contrarian Radar**: ATR-based mean-reversion scanner identifying overextended pairs.
- **Relative Strength**: Alpha leader detection comparing Altcoin performance vs BTC.
- **Dashboard Signal Overview**: New "Oracle Signal Summary" widget on the main dashboard providing instant market pulse and top 5 high-conviction signals.
- **MarketDataService**: Centralized backend engine for merging real-time Binance data with CoinGecko metadata.

### Improved

- **Analytics Performance**: Refactored data fetching to support concurrent 50+ coin analysis with <4s response times.
- **API Scalability**: Added `limit` and `timeframe` parameters to all analytics endpoints for dynamic depth control.

## [0.4.5] - 2026-01-17

### Added

- **24h Change Sorting**: Enabled sorting on the "24h" column in the main coin table.
- **Support for Multi-Timeframe Change**: Backend `/api/market/coins` now supports sorting by `change_1h` and `change_7d`.

### Fixed

- **Dashboard Sorting State Bug**: Resolved a critical issue where table sorting would incorrectly affect "Top Gainers/Losers" widgets. Widgets are now fully decoupled and pull from a dedicated `/api/market/summary` endpoint.
- **Duplicate React Keys**: Fixed "Duplicate Children with Key" console warnings by implementing symbol deduplication in the backend's data-merging logic (handling multiple blockchain versions of coins like DAI/WETH).
- **URL Parameter Cleanup**: Implemented a "Clean URL" strategy. Sorting states are initialized from URL parameters (allowing widget-to-table links) but are immediately cleaned from the address bar to prevent clutter and ensure manual refreshes reset to the default view.
- **Widget Navigation**: Fixed "View More" links in Top Gainers/Losers/Volume widgets to correctly deep-link into the main table with corresponding sort parameters.

## [0.4.0] - 2026-01-15

### Added

- **Market Indicator Cards**: Replaced StatsCards with professional dashboard indicators:
  - **BTC Volatility**: 14-day volatility with gauge and sparkline.
  - **Market ADX**: Trend strength indicator (Ranging/Trending/Strong).
  - **24h Volume**: Top 100 coins total volume with market regime.
  - **BTC Dominance**: BTC volume share among top 100 coins.
  - Tooltips explaining how to read each indicator.
  - New `/api/indicators/market/dashboard` endpoint.
  - Separated `market_indicators.py` from chart-level `calculator.py`.
- **Hybrid Market Architecture**:
  - Implemented accurate "Two-Brain" data system merging real-time Binance prices with rich CoinGecko metadata.
  - **7-Day Sparklines**: Added real historical price graphs to the main coin table (sourced from CoinGecko).
  - **Fallback Logic**: Ensuring even non-Binance coins (e.g. stETH) appear in the dashboard via Snapshot fallback.
  - **Deterministic Icons**: Added visual fallback for coins with missing logos.
- **Analytics Dashboard**: New `/analytics` page featuring professional-grade market analysis tools:
  - **Funding Rate Chart**: Visualizes funding rates across top exchanges to gauge market sentiment.
  - **Open Interest Chart**: Tracks total open interest over time.
  - **Long/Short Ratio**: Stacked bar chart showing the ratio of long vs short positions.
  - **Educational Insights**: Added "What is this?" and "Trading Tips" sections for each metric.
- ~~**Liquidation Heatmap**~~: (Removed - WebSocket service disabled without CoinGlass predictions)
- **Chart Enhancements**:
  - **Refresh Button**: Added a dedicated button to the chart header to force-refresh OHLCV and Ticker data, complete with a spinner animation.
  - **Tooltips**: Added informative tooltips to all chart header icons (Indicators, Settings, Refresh, etc.).
  - **Full-Width Layout**: Navbar now dynamically expands to full width on Chart and Analytics pages for immersive viewing.
- **Navigation**:
  - Added a "Charts" link with active state highlighting to the main Navbar.
  - Improved Navbar visibility logic to ensure it appears consistently across all pages.
- **Watchlist Enhancements**:
  - Search dropdown to find and add coins from 400+ available pairs.
  - Real-time prices and 24H change shown in search results.
  - Visual indicator for coins already in watchlist.
  - Click-to-add/remove functionality.
  - Empty state with "Add coins" prompt.
- **Coin Details Panel**: New sidebar component showing:
  - Current price with change badge.
  - Key stats: Volume, High, Low, Range (24H).
  - Visual price position bar within 24H range.
  - Performance indicator.
- **Market Cap Sorting**: Added Market Cap column to the main coin table and set it as the default sorting method.
- **Refresh Button**: Added to toolbar to scroll chart to latest candle.
- **Chart Timeframes**: Updated default timeframe to 4H and expanded quick selector options to include 12H, 3D.
- **Chart Customization**: Added a new settings modal (gear icon) to configure custom colors for candlesticks (Body, Borders, Wick) for both Up and Down candles.
- **Indicator Colors**: Added color picker to the "Add/Edit Indicator" modal, allowing users to choose custom colors for their indicators.
- **Indicator Management**: Added a quick "Remove" (X) button directly to indicator badges on the chart toolbar.
- **Indicator Editing**: Clicking an indicator badge now re-opens the settings modal for quick edits.

### Fixed

- **Data Stale Issue**: Fixed a critical backend bug where the OHLCV endpoint returned stale database records. Implemented a staleness check to force a fresh fetch from Binance if the latest candle is outdated.
- **Loading UX**: Replaced the text-based "Loading..." indicator in the chart header with a modern spinner icon (`Loader2`).
- **Navbar Duplication**: Resolved an issue where the Navbar appeared twice on the chart page by correctly managing layout nesting.

### Changed

- **Refetch Interval**: Reduced the default OHLCV data refetch interval from 60s to 15s for tighter synchronization with live prices.

### Fixed

- **Timeframe Switch Bug**: Fixed chart jumping to old historical data when switching timeframes (15m, 1h, etc.). Chart now correctly shows the most recent candles.
- **Pane Sync Error**: Fixed "Value is null" runtime error in indicator pane synchronization by adding robust null checks.
- **Theme Issues**: Fixed hardcoded dark theme colors in the "Add Indicator" modal to respect light/dark mode preferences.
- **UI Cleanup**: Removed redundant "ChevronDown" icons from the chart header dropdowns.
- **Settings Persistence**: Chart color settings are now persisted locally using Zustand.
- **Chart Architecture**: Major refactoring of `CandlestickChart` into a modular Feature Architecture using React Context (`ChartContext`, `ChartProvider`) and specialized sub-components (`ChartCanvas`, `MainChartSeries`, `ChartIndicators`) for improved maintainability and performance.

### Fixed

- **Sparkline Jitter**: Fixed an issue where sparklines in the `CoinTable` would randomly regenerate on every render/interaction. Implemented deterministic data generation seeded by coin symbol.
- **Page Scroll**: Fixed main page scrolling issue by correcting `overflow-y-auto` constraints in the main layout.
- **Chart Settings**: Fixed chart color settings (up/down colors) not applying correctly by adding missing store subscription in `ChartCanvas`.
- **Chart Loading**: Unified chart loading state to match the Analytics page design, replacing the complex skeleton with a clean spinner and text.
- **Formatter Consolidation**: Refactored core formatting logic (Prices, Volumes, Percentages) into a centralized `src/lib/formatters.ts` utility. Updated all major components (`CoinTable`, `StatsCards`, `ChartHeader`, `AnalyticsPage`, etc.) to use these standard formatters for consistent data presentation across the app.

## [0.3.0] - 2026-01-05

### Added

- **Modern Design System**: Full migration to **Tailwind CSS** and **Shadcn UI** tokens.
  - Replaced legacy CSS and `styled-jsx` with extensive utility classes.
  - Implemented **HSL-based theming** in `globals.css` for consistent dark/light mode switching.
- **Top Coins Widgets**: Added "Top Gainers," "Top Losers," and "Volume Leaders" widgets with real-time data and distinct coloring.
- **Sparklines**: Added SVG sparklines to the "Last 7 Days" column in the coin table to visualize weekly trends.
- **Volume Formatting**: Standardized volume display to Billions (B) and Millions (M) across all widgets.

### Fixed

- **UI Alignment**: Fixed horizontal alignment of price and name in `TopCoinsWidgets`.
- **Theme Colors**: Restored missing `success` (green) and `danger` (red) colors for percentage changes and sparklines by correcting HSL variable definitions.
- **Legacy Cleanup**: Removed `src/styles/components.css` and all deprecated CSS files.
- **Alignment**: Fixed vertical alignment of prices in the "Top Coins" lists.

### Changed

- **Frontend Styling**: All components (`Navbar`, `Sidebar`, `CoinTable`, `Chart`, `Modals`) now use Tailwind utility classes.
- **Sparkline Rendering**: Updated SVG stroke colors to valid `hsl()` syntax to fix invisible lines.

## [0.2.0] - 2026-01-05

### Added

- **Separate Pane Indicators**: Added support for RSI, MACD, and OBV indicators displayed in separate panes below the main chart.
  - Synchronized time scales between main chart and indicator panes.
  - Dynamic resizing of all chart panes.
- **UI Enhancements**:
  - Integrated `lucide-react` for a unified and modern icon set.
  - CoinGlass-inspired aesthetic updates to `CoinTable`, `IndicatorToolbar`, `ChartPage`.
  - Added "StatsCards" for market overview highlights.
  - Added "TopCoinsWidgets" for gaining/losing coins.
- **Market Widget Navigation**: Enabled "More >" links for Top Gainers/Losers/Volume to navigate to dedicated filtered views (`/markets/[type]`).
- **MVP Test Suite**: Implemented Playwright E2E tests for automated regression testing.
- **Documentation**: Added comprehensive **Development Guidelines** to `CONTEXT.md` covering feature addition, debugging, testing, and **continuous documentation** protocols.

- **Backend Data**:
  - Enhanced market data endpoints to provide 24h change, volume, high, and low stats.

### Fixed

- **Chart Resizing**: Fixed an issue where the chart had a fixed minimum height, causing blank space when indicators were removed. Added `ResizeObserver` for robust responsiveness.
- **Chart Synchronization**: Fixed a "Value is null" runtime error caused by race conditions in time scale synchronization when adding/removing indicators. Implemented proper subscription cleanup.
- **Analyze Button**: Fixed "Analyze" button navigation in the coin table to correctly route to the chart page.

### Changed

- **Rebranding**: Renamed "Magus Terminal" references to "Argus".
