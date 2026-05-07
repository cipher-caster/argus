---
name: Prioritized Future Roadmap (Phases 17-23)
description: Strategic prioritization for next phases - foundation first, then value, then expansion
type: project
---

## Prioritized Implementation Order

### TIER 1: Foundation & Safety ✅ COMPLETE

**Phase 17: Test Coverage — COMPLETE (99 tests)**
- Phase A: Backtest engine (14), historical resolution (39), TradeAnalyzer (14) ✅
- Phase B: Frontend E2E data rendering (9), trading page (6), navigation (6) ✅
- Phase C: Signal-position joins, regime capture, rejection analysis (11) ✅
- Files: `backend/tests/test_backtest_engine.py`, `test_signal_log.py`, `test_analyzer.py`, `test_analytics_integration.py`; `frontend/tests/data-rendering.spec.ts`, `trading.spec.ts`, `e2e.spec.ts`

---

### TIER 2: Data & Analytics Foundation ✅ COMPLETE / MOSTLY COMPLETE

**Phase 18: Data Model for Learning from Trades — COMPLETE**
- `regime_at_signal`, `regime_at_resolution`, `btc_price_at_resolution`, `time_to_resolution_ms` all in SignalLog ✅
- Rejection analysis implemented (TestRejectionAnalysis passes) ✅
- Closed in commit `ac1f079` (entry-time regime capture)

**Phase 22A: OKX Backtesting UI Integration — MOSTLY COMPLETE**
- Provider selector (Binance/OKX toggle) on trading page: ✅ `TradingConfig.tsx:73-110`
- `TRADING_PROVIDER` config in orchestrator: ✅ `orchestrator.py:28-60`
- OKX backfill job (every 30min, not daily): ✅ `worker.py:602-678`
- Dashboard OKX recommendations widget: ✗ **MISSING** (no provider-specific widget)

**Phase 22C: OKX Config Optimization — PARTIAL**
- Parameter sweeps documented: ✅ `docs/OKX_BACKTEST_REPORT.md:125-163` (SL, confidence, market state)
- OKX-specific watchlist configuration (per-exchange switching): ✗ **MISSING**
- Per-symbol overrides (FET, ATOM, STRK): ✗ **REMOVED** — `SYMBOL_OVERRIDES = {}` in `titan.py:14` (overrides degraded performance when correctly applied in v0.9.8, removed permanently)

---

### TIER 3: User-Facing Analytics & Optimization

**Phase 19: Analytics Page Redesign — ✅ COMPLETE (2026-04-09)**
- `SignalOutcomeSnapshot` table: ✅ `backend/app/schemas/snapshot.py`, migration `migrate_v0_19_0.py`
- `snapshot_signal_outcomes` arq job (00:05 UTC): ✅ `backend/app/jobs/snapshot.py`, registered in `worker.py`
- `/api/analytics/signal-outcomes/trend` endpoint: ✅ `analytics.py:802`, Redis 1hr cache, regime + conviction breakdown
- `WinRateTrend.tsx` component: ✅ SVG line chart, stat cards, breakdown pills, 3rd analytics tab
- 17 new tests in `test_snapshot_job.py` — all passing (413 total)

---

### TIER 4: Expansion & Multi-Provider Support

**Phase 21: OKX Provider Migration Analysis — NOT STARTED**
- Live paper trading comparison Binance vs OKX
- Risk assessment, WR comparison, migration strategy
- **Blocker:** Needs Phase 22A running + 1-2 weeks live data

---

### TIER 5: Polish & Documentation

**Phase 20: API Documentation & Swagger — ~30% DONE**
- Endpoint tags: ✅ All 8 domain tags in place (Analytics, Trading, Strategy, etc.)
- Response models: ⚠️ 8/18 endpoints (analytics.py complete, trading/optimization/strategy = 0)
- Example responses in schemas: ✗ None
- Docstrings: ⚠️ Analytics good, trading/optimization/strategy weak
- Missing response_model on: all 10 trading.py routes, 4 optimization.py, 3 strategy.py

**Phase 23: Advanced Features — NOT STARTED**
- Price alerts / push notifications
- WebSocket push for live ticker updates
- Multi-strategy support

---

## Summary Execution Plan

| Priority | Phase | Effort | Status |
|----------|-------|--------|--------|
| 1 | 17 (Tests A/B/C) | Medium | ✅ COMPLETE (99 tests) |
| 2A | 18 (Data Model) | Medium | ✅ COMPLETE |
| 2B | 22A (OKX UI) | Light | ✅ MOSTLY COMPLETE (missing OKX dashboard widget) |
| 2B | 22C (OKX Config) | Medium | ⚠️ PARTIAL (sweeps documented; no per-exchange watchlist; symbol overrides removed) |
| 3 | 19 (Analytics) | Medium-Heavy | ✅ COMPLETE (413 tests) |
| 4 | 21 (OKX Migration) | Medium | ❌ NOT STARTED |
| 5 | 20 (API Docs) | Light | ⚠️ ~30% DONE (tags ✓, 8/18 response_model, 0 examples) |
| 6 | 23 (Advanced) | Heavy | ❌ NOT STARTED |

## Remaining Work (Next Steps)

1. **Phase 22A finishing touch**: OKX-specific dashboard recommendations widget
2. **Phase 22C remaining**: Per-exchange watchlist switching UI (per-symbol overrides are dead — removed by design)
3. **Phase 19**: Full build — snapshot table + job + trend endpoint + WinRateTrend.tsx (read plan first)
4. **Phase 20**: Add `response_model` to 10 trading routes, 4 optimization routes, 3 strategy routes
5. **Phase 21**: Needs live OKX data collection period first
6. **Phase 23**: Long-term nice-to-have
