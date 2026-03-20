# Session Context

This document provides context for continuing development on Argus.

## Project Overview

**Argus** is a professional cryptocurrency analytics dashboard (CoinGecko/CoinGlass-style) with AI-powered trading signals for 400+ Binance pairs.

## Tech Stack

- **Backend**: FastAPI (Python 3.11), PostgreSQL, Redis, ARQ worker
- **Frontend**: Next.js 14 App Router, TanStack Query v5, Zustand, Tailwind CSS + Shadcn UI
- **Data**: Binance via CCXT, CoinGecko for metadata

## Current State (v0.9.1)

### What's Working

- **`/` Dashboard**:
  - `DashboardStatusBar` — BTC regime (BEAR/BULL), bull/bear %, top signals, Avg RSI, Market Cap, BTC Dominance
  - `BestSetups` — high-conviction Titan signals with regime filtering
  - `BTCCard` — BTC price, 24h change, 7d sparkline, high/low
  - `DashboardWatchlist` — starred coins with live prices and Titan signal badge
  - `TopMovers` — gainers and losers compact chip rows

- **`/markets` page**: Full 388-coin CoinTable with sort, pagination, search, sparklines

- **`/markets/[type]` page**: Category views (gainers, losers, volume) with sort defaults

- **`/chart/[symbol]` Chart page**:
  - TradingView Lightweight Charts candlestick chart
  - Timeframes: 1m, 5m, 15m, 1h, 4h, 12h, 1d, 1w
  - Indicators: EMA, SMA, BBands (overlay), RSI, MACD, OBV (separate panes)
  - Watchlist with search and drag-drop reordering
  - `CoinDetailsPanel`: regime, Titan signal + advice
  - `CoinSignalIntel`: backtest stats + open signals per coin
  - `CoinAnalysisModal`: deep analysis with signal track record

- **`/analytics` page** (5 tabs):
  - Best Setups (Titan regime-filtered, conviction + win rate + MTF confluence)
  - Screener (Oracle Earnest score, bias, state per coin)
  - Signal Log (live/scanner/backtest source filter, per-signal outcome tracking)
  - Backtest Performance (per-coin win rate / R-multiples)
  - Titan Radar (current Titan signals)

- **`/trading` page**:
  - Portfolio summary (balance, PnL, unrealized, exposure)
  - Active positions table with live PnL
  - Trade history with outcome badges
  - Equity curve chart
  - Risk settings panel (position size, max DD, conviction threshold)
  - Activity feed (system events)

- **Paper Trading Engine**:
  - Signal → Position lifecycle (PENDING → OPEN → CLOSED)
  - Risk manager (drawdown, conviction, correlated, min order size)
  - Position sizing (2% risk per trade, 2:1 RR)
  - TP/SL hit detection via candle walk
  - Manual close and close-all

- **Signal Pipeline**:
  - Worker scans watchlist at 4H candle close with regime-based filtering
  - Scanner logs best setups from Titan radar
  - Outcome resolution via candle walk (WIN/LOSS/REVIEW)
  - Signal log config (watchlist, confidence threshold, market gates)

- **Test Suite**: 229 backend pytest tests across all modules

## How to Run

```bash
# Docker (recommended)
docker-compose up -d --build

# Services: Frontend :3000 | Backend :8000 | Redis :6379 | Postgres :5433
```

Database: `postgresql://argus:argus_password@localhost:5433/argus_db`

## Key Files

### Backend (`/backend/app/`)

| File | Purpose |
|---|---|
| `main.py` | FastAPI app entry, router setup |
| `routes/analytics.py` | Analytics endpoints (screener, signal-log, best-setups, titan-radar) |
| `routes/strategy.py` | Oracle + Titan strategy endpoints, candle data |
| `routes/trading.py` | Trading API (portfolio, positions, history, config, close) |
| `routes/market.py` | Market data (ohlcv, tickers, coins, summary) |
| `routes/indicators.py` | Indicator calculation + dashboard |
| `routes/system.py` | Activity log |
| `jobs/signal_log.py` | Worker: signal logging + outcome resolution |
| `strategies/oracle.py` | Oracle Prophet v9.0 |
| `strategies/titan.py` | Titan Unified System |
| `trading/orchestrator.py` | Trade lifecycle (signal → position → close) |
| `trading/risk_manager.py` | Risk gates (drawdown, conviction, correlated) |
| `trading/portfolio.py` | Balance tracking, equity curve, stats |
| `trading/backtest.py` | Backtest engine |
| `indicators/screener.py` | Oracle screener batch runner |
| `services/market_data.py` | Cache-aware data fetching |
| `providers/binance_provider.py` | CCXT Binance wrapper |
| `schemas/signal_log.py` | SignalLog SQLModel |
| `schemas/trading.py` | Position + TradeEvent SQLModels |
| `schemas/analytics.py` | Pydantic response models |
| `exceptions.py` | Custom exception hierarchy |

### Frontend (`/frontend/src/`)

| File | Purpose |
|---|---|
| `app/page.tsx` | Dashboard |
| `app/markets/page.tsx` | Full coin table |
| `app/markets/[type]/page.tsx` | Category pages (gainers/losers/volume) |
| `app/chart/[symbol]/page.tsx` | Chart view |
| `app/analytics/page.tsx` | Analytics tabs |
| `app/trading/page.tsx` | Trading dashboard |
| `components/trading/` | Portfolio, Positions, History, EquityCurve, Config, ActivityFeed |
| `components/analytics/` | BestSetups, SignalLog, BacktestPerformance |
| `components/features/dashboard/` | Dashboard widgets |
| `hooks/useAnalyticsData.ts` | Analytics API hooks |
| `hooks/useTradingData.ts` | Trading API hooks |
| `hooks/useMarketOverview.ts` | Market data hooks |
| `lib/api.ts` | API types + fetch functions |
| `lib/marketApi.ts` | Market-specific API functions |
| `stores/` | Zustand stores |

## Development Guidelines

### Adding New Features

- **Backend First**: Define schema → route → service. Always check Redis before hitting Binance.
- **Frontend**: Add type to `lib/api.ts` → add hook to `hooks/` → use in component.
- **Error Handling**: Always raise from the `exceptions.py` hierarchy (`DataProviderError` → 503, `ValidationError` → 400).

### Testing

```bash
# Backend
docker compose exec -e PYTHONPATH=/app backend pytest -v

# Type check frontend
cd frontend && npx tsc --noEmit
```

### Debugging

```bash
docker compose logs backend -f
docker compose exec redis redis-cli  # check cache keys
docker compose exec db psql -U argus  # check DB
```

### Documentation

Always update `CHANGELOG.md` and this file when adding features or making architectural changes.
