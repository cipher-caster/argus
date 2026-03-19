# Changelog

All notable changes to this project will be documented in this file.

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
