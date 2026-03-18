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
- [x] 119 backend tests (oracle, titan, analytics, market, worker, screener)
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

### Phase 13: Chart Signal Intelligence
- [ ] CoinSignalIntel sidebar panel on chart deep-dive page
- [ ] Per-coin backtest stats card (WR, R-profit, status badge) in sidebar
- [ ] Recent signals list for current coin (last 5–10, live + backtest)
- [ ] Open signal highlight with TP/SL distance from current price

### Phase 14: Test Coverage
- [ ] Unit tests for signal log worker jobs (log_watchlist_setups, resolve_signal_outcomes)
- [ ] Unit tests for market gate logic (_passes_market_gate with config permutations)
- [ ] Unit tests for backtest stats aggregation endpoint
- [ ] Frontend component tests (BacktestPerformance, SignalLog, CoinSignalIntel)
- [ ] E2E tests: Analytics page tab navigation and data rendering
- [ ] E2E tests: Signal Log filter/dropdown interaction
- [ ] E2E tests: Backtest row expand/collapse with signal detail fetch
- [ ] E2E tests: Chart page sidebar with signal intel panel

### Phase 15: Advanced Features
- [ ] Portfolio tracking & user accounts
- [ ] Price alerts / push notifications
- [ ] WebSocket push for live ticker updates

---

## Cancelled

### Drawing Tools ~~(Paused)~~
- ~~Trendlines, Fibonacci retracements, rectangles~~
- Removed in v0.6.0 — DrawingToolbar column removed from chart layout. Chart now full-width.
