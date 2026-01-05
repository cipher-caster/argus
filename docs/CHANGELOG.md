# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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

### Changed

- **Drawing Toolbar**: Simplified to show only cursor and refresh icons (removed non-functional drawing tools).

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
