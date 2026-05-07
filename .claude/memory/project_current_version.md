---
name: Current Project Version & State
description: v1.1.4 — Execution-Layer Defense-in-Depth & Staleness Gate; 15-coin watchlist active.
type: project
originSessionId: 1f5b6b5a-ea47-4ba9-87d4-8690f44ca852
---
## v1.1.4 — 2026-04-26 — Execution-Layer Defense-in-Depth & Staleness Gate

**Watchlist: 15 coins** — BTC, ETH, BNB, TRX, XRP, FET, NEAR, ATOM, DOGE, STRK, POL, AVAX, SUI, RENDER, AAVE.

## v1.1.3 — 2026-04-25 — Watchlist Update

**ARB out, SUI/RENDER/AAVE in.**

- SUI: 48.4% WR / 32 signals, RENDER: 47.2% WR / 37 signals, AAVE: 60.0% WR / 10 signals
- ARB removed: 36.1% WR over 83 signals
- DEFAULT_COINS in backtest_engine.py synced

## v1.2.0 — 2026-04-19 — P0 Trading Correctness

**All historical signal_log rows tagged v1 (legacy). New signals are v2. 418 backend tests passing.**

- MSS lookahead eliminated: `_mss_to_list` now backward-only pivot detection.
- Forming-candle bias fixed at provider layer (Binance + OKX drop last row).
- Sharpe, Sortino, Calmar, return_std, max_drawdown_r added to compute_stats + PortfolioTracker.
- methodology_version column on signal_log; analytics defaults to v2 only.
- 1,679 existing rows backfilled to v1 via migrate_v1_methodology.py.
- Review checkpoint scheduled: ~2026-06-01 (see ROADMAP.md and project_v2_methodology_review.md).

## v1.1.0 — 2026-04-09 — Phase 19 closeout

**Daily win-rate snapshot system live.**

- New table `signal_outcome_snapshot` (migration `migrate_v0_19_0.py`).
- Arq cron job `snapshot_signal_outcomes` at 00:05 UTC — idempotent, aggregates by (regime, conviction_band, source, coin).
- `/api/analytics/signal-outcomes/trend` endpoint with Redis cache (1hr TTL), regime + conviction breakdowns.
- `WinRateTrend.tsx` SVG line chart wired as 3rd analytics tab with stat cards, breakdown pills, legend.
- 413 backend tests passing.
- Phase 19 fully closed.

## v1.0.0-alpha+ — 2026-04-07 — Phase 18 closeout

**Entry-time regime context now captured at signal fire time.**

- New columns `signal_log.regime_at_signal` + `btc_price_at_signal` (migration `migrate_v0_9_3.py`).
- Populated in all three sources: `log_watchlist_setups`, `log_best_setups`, `log_contrarian_signals`.
- Surfaced in `SignalDetailModal` as 2x2 Market Context grid with regime-shift indicator.
- 396 backend tests passing.

## v1.0.0-alpha — 2026-04-05

**First alpha release. Dashboard fully polished.**

**Key changes:**
- Shared `CardError` component — consistent offline UI across all dashboard cards
- All cards have proper loading skeletons and error states
- No more silent nulls or misleading empty/zero states when backend is offline

## v0.9.9 — 2026-04-05

**Dashboard layout redesign.**

**Key changes:**
- Row order: Status Bar → Best Setups + BTC/Watchlist → Active Signals (60%) + Paper Trading (40%) → Top Movers
- Active Signals: column headers (Entry/TP/SL/Conv./Age), fixed-width left-aligned columns
- Paper Trading: tooltip, chevron nav link, Pending label fix, unified card style
- Best Setups: fixed center column spacing, chevron analytics link
- Top Movers: two rows (gainers/losers), 10 coins each, hidden scrollbar, moved to bottom
- All dashboard tooltips: side=bottom align=start

## v0.9.8 — 2026-04-05 (PREV LATEST)

**392 backend tests passing. Pre-production hardening complete.**

**Key changes:**
- Batch race condition fix: `process_signal()` accepts `batch_positions` to prevent exposure gate bypass
- Risk params tightened: 3% risk/trade, 2x leverage, 200% exposure cap, 12% drawdown, 16h expiry
- ADX(14) added to Titan `_add_indicators()` (observe-only, no gate)
- Paper trading reset to $200 for 7-day observation (Apr 4–11)
- Pre-prod audit: docs/market-reports/2026-04-04-pre-prod-audit.md
- Data backed up: docs/trading/*_backup_2026-04-04.csv

## v0.9.9 — 2026-03-28

**367 backend tests passing. Entry tolerance gate removed.**

**Key changes:**
- Entry tolerance gate removed from orchestrator — was rejecting valid PENDING positions on temporary price drift; LIMIT signals wait at intended_entry via check_pending_fills anyway
- DB connection pool: pool_size=10, pre_ping, recycle=3600
- BTC regime cached in Redis (1hr TTL, key `market:regime`) — shared across analytics + signal_log
- Dashboard indicators endpoint caches in Redis (5min TTL)
- Worker `_retry()` helper (3 attempts, 2s delay) on exchange/HTTP calls
- Bulk pg_insert().on_conflict_do_update() replaces N+1 session.merge() in market_data.py
- Orchestrator commit error handling (rollback on check_pending_fills/open_positions/circuit_breaker)
- Raw str(e) sanitised from all HTTP 500/503 responses
- apply_experiment wrapped with Redis rollback on partial failure
- CORS whitelist, TradingConfigUpdate bounds, timeframe validation on 4 analytics endpoints
- Hardcoded DB credential fallback removed (RuntimeError if DATABASE_URL not set)
- Startup validation: lifespan raises RuntimeError on DB/provider init failure
- asyncio.Semaphore(10) on fetch_all_candles — caps concurrent exchange calls
- Shared utilities: app/utils/trading_utils.py (calculate_conviction), app/constants.py (TIMEFRAME_MS)
- Full audit report: docs/backend/AUDIT_2026_03_28.md

**Remaining audit backlog (low urgency):**
- 0 tests for providers/, notifier.py, storage.py, main.py
- Orchestrator tests use MagicMock — don't test real SQLAlchemy

## v0.9.8 — 2026-03-27

**Key fixes:** SYMBOL_OVERRIDES lookup bug fixed (key format was "BTC/USDTUSDT"); overrides removed after confirmed harmful when applied. TP=2.0x universal. RiskManager sizing fix. Tiebreaker WIN/LOSS inversion fixed.

## v0.9.6 — 2026-03-27

**Key fixes:** Provider singleton, hardcoded provider tag, tiebreaker closed-provider bug, DataProvider ABC.

## v0.9.5 — 2026-03-27

Market-fill entry + notional position sizing. Entry tolerance gate added (later removed in v0.9.9).

## v0.9.4 — 2026-03-26

Counter-regime signal tracking. Scanner conviction threshold 60→50.
