# Session Context

This document provides context for continuing development on Argus.

## Project Overview

**Argus** is a professional cryptocurrency dashboard similar to CoinGecko/CoinGlass.

## Tech Stack

### Infrastructure

- **Docker Compose**: Orchestrates all services (API, Worker, Redis, DB).
- **PostgreSQL**: Persistent history.
- **Redis**: Real-time cache & Job Queue.

### Backend

- **Framework**: FastAPI (Python 3.10+)
- **Worker**: Python Background Service (Arq)
- **Providers**: Binance (CCXT), CoinGecko

### Frontend

- **Framework**: Next.js 14 (App Router)
- **State**: React Query + Zustand
- **Styling**: Tailwind CSS + Shadcn UI

## Current State

### What's Working

- ✅ Market Overview landing page at `/`
  - **New UI**: Professional layout with "Stats Cards" and "Top Coins" widgets.
  - **Sorting**: Enhanced sorting by Price, Volume, Market Cap, and 24h Change.
- ✅ Coin table with 400+ USDT pairs from Binance
  - **Live Data**: Real-time prices, percentage changes (Green/Red indicators), and market cap.
  - **Sparklines**: Mini trend charts for 7-day performance (Red/Green based on trend).
- ✅ Sort by price (default: high to low), symbol
- ✅ Search and pagination (50 per page)
- **Interactive Chart (`/chart/[symbol]`)**:
  - TradingView-style candlestick chart using `lightweight-charts`.
  - **Customization**: Users can configure candle colors (Body, Border, Wick) via a "Settings" modal.
  - **Indicators**: Support for overlay indicators (SMA, EMA, BBands) and separate pane indicators (RSI, MACD, OBV).
    - Custom color selection for indicators.
    - Interactive badges to Edit/Remove indicators directly from the chart.
  - **Timeframes**: 1m, 5m, 15m, 1h, 4h, 1d, 1w.
  - **Toolbar**: Cursor mode + Refresh button to scroll to latest candle.
  - **Watchlist**: Add/remove coins with search dropdown. Persisted in localStorage. Drag-drop reordering.
  - **Coin Details Panel**: Shows key stats (Volume, High, Low, Range), 24H price position, and performance.
- ✅ Market Cap sorting on main page (default)
- ✅ Dark/Light theme toggle (HSL-based theming)
- ✅ Real-time price updates
- ✅ Automated Test Coverage (Playwright)
- ✅ **AI Integration (Argus Oracle v9.0)**:
  - **Earnest Brain**: 4-voter confluence engine (RSI, Bollinger, ADX, EMA).
  - **Prophet Strategy**: Trend-following logic with daily filters.
  - **Live Backtesting**: Real-time simulation of strategies on chart history.
  - **Signal Markers**: Buy/Sell arrows on candles.
- ✅ **Analytics Dashboard**:
  - Funding Rates, Open Interest, and Long/Short Ratios.
  - Professional charts for market sentiment.

### How to Run

**Using Docker (Recommended)**

```bash
docker-compose up -d --build
```

This starts:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Worker**: Background data ingestion
- **Redis**: Port 6379
- **Postgres**: Port 5433

**Database Credentials**

- **Host**: `localhost`
- **Port**: `5433` (mapped from 5432)
- **User**: `argus`
- **Password**: `argus_password`
- **Database**: `argus_db`
- **Connection URL**: `postgresql://argus:argus_password@localhost:5433/argus_db`

**Manual Run (Dev)**

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Terminal 3 - Worker
cd backend
source venv/bin/activate
python -m app.worker
```

## Key Files

### Backend (`/backend/app/`)

| File                            | Purpose                    |
| ------------------------------- | -------------------------- |
| `main.py`                       | FastAPI app entry          |
| `providers/binance_provider.py` | CCXT Binance data          |
| `routes/market.py`              | Coins list, OHLCV, tickers |
| `routes/indicators.py`          | Technical indicators API   |
| `indicators/calculator.py`      | pandas-ta calculations     |

### Frontend (`/frontend/src/`)

| File                              | Purpose                        |
| --------------------------------- | ------------------------------ |
| `app/page.tsx`                    | Market Overview landing        |
| `app/chart/[symbol]/page.tsx`     | Chart view                     |
| `app/globals.css`                 | Global styles & HSL theme vars |
| `tailwind.config.ts`              | Tailwind theme config          |
| `components/TopCoinsWidgets.tsx`  | Top Gainers/Losers/Vol widgets |
| `components/CoinTable.tsx`        | Coins table                    |
| `components/CandlestickChart.tsx` | TradingView chart              |
| `components/IndicatorToolbar.tsx` | Indicator management           |
| `stores/themeStore.ts`            | Dark/light mode                |
| `stores/indicatorStore.ts`        | Indicator state                |
| `lib/marketApi.ts`                | Market API client              |
| `lib/utils.ts`                    | Tailwind `cn` utility          |

## Paused Features

### Drawing Tools

Code exists but hidden from UI:

- `stores/drawingStore.ts` - Zustand store
- `components/drawing/DrawingCanvas.tsx` - Canvas overlay
- `components/drawing/DrawingToolbar.tsx` - Tool selector

To re-enable: import `DrawingToolbar` in chart page and `DrawingCanvas` in `CandlestickChart.tsx`.

## Next Steps (from ROADMAP.md)

### Routing

| Route             | Component       |
| ----------------- | --------------- |
| `/`               | Market Overview |
| `/chart/[symbol]` | Chart View      |

## Development Guidelines

To prevent regressions and ensure stability, follow these steps when adding features or debugging:

### 1. Adding New Features

- **Backend First**: Verify `backend/app/routes/*.py` for input validation.
  - _Example_: If adding a sort field, add it to the regex pattern in `Query(pattern="...")`.
- **Frontend Sync**: Ensure query parameters match the backend requirements exactly.
- **Route Verification**: If adding pages, verify dynamic routes (e.g., `[symbol]`) are reachable.

### 2. Debugging Errors

- **Check Network Tab**: Look for `422 Unprocessable Entity` - this usually means Frontend sent a param the Backend rejected.
- **Check Server Logs**: `uvicorn` logs provide detailed validation errors.
- **Isolate**: Test the API endpoint directly via Swagger (`http://localhost:8000/docs`) before debugging React components.

### 3. Testing Requirements

- **Mandatory E2E**: ALways run the full test suite before committing:
  ```bash
  npx playwright test
  ```
- **New Links**: If adding navigation links, add a corresponding test case in `tests/e2e.spec.ts`.
- **Manual Verification**: Use the Browser Tool to verify "happy paths" for complex visual changes (like charts).

### 4. Continuous Documentation

- **Update Protocols**: Always update `docs/CONTEXT.md` and `docs/CHANGELOG.md` with:
  - New features or architectural changes.
  - New debugging skills or critical fix patterns.
  - Any "gotchas" discovered during development.

## Next Steps

1. Complete drawing tools (trendlines, fib retracements) - _Paused_
2. Portfolio tracking & User Accounts
3. Real-time Radar Scanner / Screener
4. WebSocket push for ticker updates
