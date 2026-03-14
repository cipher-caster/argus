# Session Context

This document provides context for continuing development on Argus.

## Project Overview

**Argus** is a professional cryptocurrency analytics dashboard (CoinGecko/CoinGlass-style) with AI-powered trading signals for 400+ Binance pairs.

## Tech Stack

- **Backend**: FastAPI (Python 3.11), PostgreSQL, Redis, ARQ worker
- **Frontend**: Next.js 14 App Router, TanStack Query v5, Zustand, Tailwind CSS + Shadcn UI
- **Data**: Binance via CCXT, CoinGecko for metadata

## Current State (v0.6.1)

### What's Working

- **`/` Dashboard**:
  - `DashboardStatusBar` — Oracle market state, bull/bear %, top signals, Avg RSI, Market Cap, BTC Dominance
  - `ActiveSetups` — top 5 Best Setups (Oracle + Titan aligned, 4H)
  - `BTCCard` — BTC price, 24h change, 7d sparkline, high/low
  - `DashboardWatchlist` — starred coins with live prices and Oracle score badge
  - `TopMovers` — gainers and losers compact chip rows

- **`/markets` page**: Full 50-coin CoinTable with sort, pagination, Oracle score badge

- **`/chart/[symbol]` Chart page**:
  - TradingView Lightweight Charts candlestick chart
  - Timeframes: 1m, 5m, 15m, 1h, 4h, 12h, 1d, 1w
  - Indicators: EMA, SMA, BBands (overlay), RSI, MACD, OBV (separate panes)
  - Watchlist with search and drag-drop reordering
  - `CoinDetailsPanel`: Oracle Earnest Score, macro Bias, Titan signal + advice

- **`/analytics` page** (5 tabs):
  - Oracle Screener (Earnest score, bias, state per coin)
  - Titan Signals (Titan radar scanner)
  - Titan Scanner (full Titan analysis table)
  - Contrarian Radar (ATR mean reversion)
  - Relative Strength (vs BTC benchmark)
  - Best Setups (Oracle + Titan high-conviction filter with win rate + MTF confluence)

- **Strategies**:
  - Oracle Prophet v9.0 (Earnest Brain -4/+4 + Daily macro filter)
  - Titan Unified System (trend + momentum, BUY/SELL/WAIT signals)
  - Live backtesting (2:1 RR, win rate displayed on Best Setups cards)
  - Eliz+Mayne MTF confluence (4H/1D/12H/1W Titan confirmation)

- **Test Suite**: 119 backend pytest tests across oracle, titan, analytics, market, worker, screener

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
| `routes/analytics.py` | All analytics endpoints |
| `routes/strategy.py` | Oracle + Titan strategy endpoints |
| `strategies/oracle.py` | Oracle Prophet v9.0 |
| `strategies/titan.py` | Titan Unified System |
| `indicators/screener.py` | Oracle screener batch runner |
| `indicators/mean_reversion.py` | Contrarian Radar logic |
| `indicators/relative_strength.py` | Relative Strength vs BTC |
| `services/market_data.py` | Cache-aware data fetching |
| `providers/binance_provider.py` | CCXT Binance wrapper |
| `schemas/analytics.py` | Pydantic models for all analytics |
| `exceptions.py` | Custom exception hierarchy |

### Frontend (`/frontend/src/`)

| File | Purpose |
|---|---|
| `app/page.tsx` | Dashboard |
| `app/markets/page.tsx` | Full coin table |
| `app/chart/[symbol]/page.tsx` | Chart view |
| `app/analytics/page.tsx` | Analytics tabs |
| `components/features/dashboard/` | Dashboard components |
| `components/analytics/BestSetups.tsx` | Best Setups cards |
| `components/analytics/OracleScreener.tsx` | Screener table |
| `hooks/useAnalyticsData.ts` | TanStack Query analytics hooks |
| `lib/api.ts` | All API types + fetch functions |
| `stores/` | Zustand stores (theme, indicators, watchlist, chart) |

## Development Guidelines

### Adding New Features

- **Backend First**: Define schema → route → service. Always check Redis before hitting Binance.
- **Frontend**: Add type to `lib/api.ts` → add hook to `hooks/` → use in component.
- **Error Handling**: Always raise from the `exceptions.py` hierarchy (`DataProviderError` → 503, `ValidationError` → 400).

### Testing

```bash
# Backend
docker compose exec backend pytest -v

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
