# Roadmap

## Completed ✓

### Phase 1: Core Infrastructure
- [x] FastAPI backend with CCXT integration
- [x] Next.js frontend with TypeScript
- [x] Binance provider support

### Phase 2: Charting
- [x] TradingView Lightweight Charts integration
- [x] Symbol and timeframe selectors
- [x] Real-time price updates

### Phase 3: Indicators
- [x] Backend indicator calculator (pandas-ta)
- [x] Overlay indicators: EMA, SMA, Bollinger Bands
- [x] Indicator toolbar with add/edit/remove
- [x] Color customization

### Phase 4: Market Overview
- [x] CoinGecko-style landing page
- [x] Coin table with sorting and search
- [x] Pagination (50 coins per page)
- [x] Click-to-chart navigation
- [x] Dark/light theme toggle
- [x] Tailwind CSS + Shadcn UI design system

### Phase 5: Separate Pane Indicators
- [x] RSI, MACD, OBV in separate panes below chart
- [x] Resizable panes

### Phase 6: Analytics Dashboard
- [x] Funding Rates, Open Interest, Long/Short Ratio charts
- [x] Watchlist with live prices
- [x] Oracle Screener (Earnest score -4 to +4)
- [x] Titan Radar (trend + momentum scanner)
- [x] Contrarian Radar (mean reversion)
- [x] Relative Strength (vs BTC benchmark)
- [x] Signal Summary (market state)

### Phase 7: AI Strategies
- [x] Oracle Prophet v9.0 (Earnest Brain + Macro Filter)
- [x] Titan Unified Strategy (trend + momentum signals)
- [x] Live backtesting with win rate + net PnL
- [x] Oracle score badge on CoinTable and DashboardWatchlist

### Phase 8: Dashboard Redesign (v0.6.0)
- [x] DashboardStatusBar (Oracle state, bull/bear %, top signals)
- [x] ActiveSetups (top 5 best setups on dashboard)
- [x] BTCCard + DashboardWatchlist with shared cache
- [x] TopMovers (gainers/losers chips)
- [x] /markets page for full coin table
- [x] ArgusLogo SVG component
- [x] Space Grotesk + DM Mono fonts

### Phase 9: Best Setups + MTF Confluence
- [x] Best Setups endpoint: Oracle + Titan high-conviction filter
- [x] Oracle backtest win rate on setup cards (≥50% green, 33–49% yellow, <33% red)
- [x] Eliz + Mayne MTF confluence (4H/1D/12H/1W Titan confirmation)

### Phase 10: Test Suite
- [x] 216 backend tests (oracle, titan, analytics, market, worker, screener, signal log, trading routes, indicator routes)
- [x] TypeScript type coverage

---

## Planned

### Phase 11: Signal History Log ✓
- [x] Worker job logs every Best Setup that fires (symbol, direction, entry, tp, sl, conviction)
- [x] 4H candle close schedule (6 scans/day) + startup scan
- [x] Outcome resolution every 30 min (WIN / LOSS / REVIEW at 7d)
- [x] Market gate system (block SLEEPING/VOLATILE, macro guard, BTC sell filter)
- [x] Configurable settings UI (watchlist, min confidence, review days, gates)
- [x] 11-coin watchlist from 20-coin backtest sweep (BTC, ETH, BNB, TRX, XRP, FET, NEAR, ARB, ATOM, DOGE, APT)

### Phase 12: Backtest Leaderboard + UI Polish ✓
- [x] Backtest Performance leaderboard with per-coin stats (WR, R-profit, L/S split)
- [x] Expandable coin rows showing individual signal history
- [x] Signal Log dropdown filter (replaced button row)
- [x] Date/time display instead of relative age
- [x] Active Signals dashboard widget (open live signals)

### Phase 13: Chart Signal Intelligence ✓
- [x] CoinSignalIntel sidebar panel on chart deep-dive page
- [x] Per-coin backtest stats card (WR, R-profit, status badge) in sidebar
- [x] Recent signals list for current coin (last 5–10, live + backtest)
- [x] Open signal highlight with TP/SL distance from current price

### Phase 14: Paper Trading Engine ✓
- [x] Position and TradeEvent SQLModel tables (PENDING → OPEN → CLOSED/EXPIRED lifecycle)
- [x] TradeOrchestrator: signal → position, pending fills, TP/SL exits, circuit breaker
- [x] RiskManager: position sizing, concurrent limits, correlation groups, conviction gate
- [x] PortfolioTracker: real-time P&L, drawdown, position value from live tickers
- [x] /trading frontend page with positions, trade history, portfolio stats, config
- [x] /portfolio and /trade slash commands
- [x] Scanner signal consolidation: log_best_setups worker job, scanner → paper trades

### Phase 15: Trading Optimization System ✓
- [x] BacktestConfig + reusable backtest_engine.py
- [x] OptimizationExperiment table (23 fields)
- [x] optimize_trading.py CLI with 5 presets (sl_sweep, tp_sweep, confidence_sweep, gate_sweep, full_grid)
- [x] TradeAnalyzer: backtest vs live comparison, config recommendations
- [x] API routes for experiments, best config, apply
- [x] /optimize slash command
- [x] docs/trading/knowledge.md with confirmed findings

### Phase 16a: BTC Timeframe Analysis & Per-Symbol Overrides (v0.8.2) ✓
- [x] BTC multi-timeframe backtest (15m, 1h, 4h, 1d) across Oracle and Titan
- [x] ETH multi-timeframe backtest — Oracle negative, Titan positive with fixed TP
- [x] Per-symbol risk overrides in Titan (SYMBOL_OVERRIDES: BTC SL=1.75x/TP=4.0x, ETH TP=4.0x)
- [x] Parameter sweep: 6 SL × 7 TP × 5 confidence thresholds on 4H
- [x] Analysis scripts: btc_timeframe_analysis, btc_4h_sweep, btc_titan_deep_dive, eth_full_analysis

### Phase 16b: Regime Detection & Oracle Deprecation (v0.9.0) ✓
- [x] BTC weekly EMA50 regime detection system (`GET /api/strategy/regime`)
- [x] DashboardStatusBar regime modal with actionable advice, aligned setups, execution guidance
- [x] Signal logging uses regime-based direction filtering (BEAR→SHORT, BULL→LONG) instead of Oracle market gate
- [x] Best Setups rewritten: Titan-only, regime-filtered, no Oracle dependency
- [x] CoinAnalysisModal and CoinDetailsPanel switched to regime + Titan (removed Oracle)
- [x] Analytics reduced to 3 tabs (Best Setups, Signal Log, Backtest Performance)
- [x] Candle-based TP/SL resolution in signal log and paper trading orchestrator
- [x] Oracle removed from all UI (backend code preserved for future experiments)
- [x] Contrarian Radar and OracleScreener removed from analytics
- [x] Dead code registry (docs/DEAD_CODE.md)

---

## Planned

### Phase 17: Test Coverage (In Progress) — see [TEST_PLAN.md](TEST_PLAN.md)
- [x] Unit tests for signal log worker jobs (log_watchlist_setups, log_best_setups, resolve_signal_outcomes) — 28 tests
- [x] Unit tests for market gate logic (_passes_market_gate with config permutations) — 6 tests
- [x] Unit tests for trading API routes (all 9 endpoints) — 18 tests
- [x] Unit tests for indicator + system routes (calculate, dashboard, activity log) — 10 tests
- [x] Unit tests for signal log stats + optimization + trade analysis — 14 tests
- [ ] Phase A: Backtest engine, historical resolution, TradeAnalyzer integration (~19 tests)
- [ ] Phase B: E2E data rendering, trading page, error resilience (~18 tests)
- [ ] Phase C: API contract snapshot tests (~6 tests)

### Phase 18: Data Model for Learning from Trades
- [ ] Add `regime_at_resolution` + `btc_price_at_resolution` to SignalLog schema — capture market context when a signal resolves, not just when it fires
- [ ] Log rejected signals — persist to signal_log with `outcome: "REJECTED"` and `rejection_reason` field (low_conviction, exposure_cap, stablecoin_vol_gate, etc.)
- [ ] Add `market_state_at_close` to Position schema — regime may change between open and close
- [ ] Expand TradeEvent types — add FILLED, PENDING, RISK_REJECTED alongside existing TP_HIT/SL_HIT
- [ ] Add `time_to_resolution_ms` to SignalLog — fast resolution = strong signal, useful for learning
- [ ] Build signal→position analytics — join signal outcomes to actual position P&L for "did the signal win AND did we make money?"

### Phase 19: Analytics Page Redesign — Trading Performance Intelligence
- [x] Remove redundant "Backtest" tab — it's just SignalLog filtered to `source=backtest`, already covered by SignalLog's source filter ✓
- [ ] Persist signal-outcomes snapshots (daily) — current `GET /api/analytics/signal-outcomes` computes on-the-fly. Need a periodic job (cron/daily) that snapshots win rate by regime, conviction band stats, rejection counts to a DB table so we can track trends over time (e.g. "win rate by regime last week vs this week")

### Phase 20: API Documentation & Swagger
- [ ] Add FastAPI auto-generated Swagger/OpenAPI docs — already available at `/docs` but needs cleanup
- [ ] Add response models (response_model) to all endpoints — many endpoints return raw dicts/JSON, should use Pydantic response models for type safety and documentation
- [ ] Add docstrings to all route handlers — many are missing descriptions
- [ ] Tag endpoints by domain (Trading, Analytics, Market, Strategy, System) for organized Swagger UI
- [ ] Add example responses to schemas for Swagger "Try it out" feature
- [ ] Redesign analytics page around trading performance (not signal browsing)
  - Win rate breakdown by strategy / coin / market condition
  - PnL curve and drawdown tracking over time
  - Risk gate audit: which gates are firing, are they helping or blocking good trades?
  - Signal quality trends over time (conviction vs outcome correlation)
  - Rejected signal analysis — how many, why, did any go on to win?
- [ ] Dashboard for user (mjm) to observe AI trader performance at a glance

**Goal:** The analytics page should serve two audiences — Claude as the AI trader (feedback loop to improve), and the user as the observer (visibility into how trading is going). Current page is designed for a human browsing signals, which is no longer the primary use case. The data model needs to capture resolution-time context so we can actually learn what works.

### Phase 21: Advanced Features
- [ ] Price alerts / push notifications
- [ ] WebSocket push for live ticker updates
- [ ] Multi-strategy support (compare Oracle vs Titan vs custom)

---

## Cancelled

### Drawing Tools ~~(Paused)~~
- ~~Trendlines, Fibonacci retracements, rectangles~~
- Removed in v0.6.0 — DrawingToolbar column removed from chart layout. Chart now full-width.
