# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - Unreleased

### Added

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

### Fixed

- **Data Stale Issue**: Fixed a critical backend bug where the OHLCV endpoint returned stale database records. Implemented a staleness check to force a fresh fetch from Binance if the latest candle is outdated.
- **Loading UX**: Replaced the text-based "Loading..." indicator in the chart header with a modern spinner icon (`Loader2`).
- **Navbar Duplication**: Resolved an issue where the Navbar appeared twice on the chart page by correctly managing layout nesting.

### Changed

- **Refetch Interval**: Reduced the default OHLCV data refetch interval from 60s to 15s for tighter synchronization with live prices.

### Added

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
