# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- **Separate Pane Indicators**: Added support for RSI, MACD, and OBV indicators displayed in separate panes below the main chart.
  - Synchronized time scales between main chart and indicator panes.
  - Dynamic resizing of all chart panes.
- **UI Enhancements**:
  - Integrated `lucide-react` for a unified and modern icon set.
  - CoinGlass-inspired aesthetic updates to `CoinTable`, `IndicatorToolbar`, and `ChartPage`.
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
