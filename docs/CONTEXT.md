# Session Context

This document provides context for continuing development on Argus.

## Project Overview

**Argus** is a professional cryptocurrency dashboard similar to CoinGecko/CoinGlass.

## Current State

### What's Working

- ✅ Market Overview landing page at `/`
- ✅ Coin table with 400+ USDT pairs from Binance
- ✅ Sort by price (default: high to low), symbol
- ✅ Search and pagination (50 per page)
- ✅ Chart view at `/chart/[symbol]` (e.g., `/chart/BTC-USDT`)
- ✅ Technical indicators: EMA, SMA, Bollinger Bands, RSI, MACD
- ✅ Separate Pane Indicators: RSI, OBV, MACD (synchronized)
- ✅ Modern UI with Lucide Icons and Market Stats

- ✅ Dark/Light theme toggle
- ✅ Real-time price updates
- ✅ Automated Test Coverage (Playwright)

### How to Run

```bash
# Terminal 1 - Backend
cd /home/mjm/Documents/argus/backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd /home/mjm/Documents/argus/frontend
npm run dev

# Run Tests
npx playwright test
```

- **App**: http://localhost:3000
- **API**: http://localhost:8000/docs

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

| File                              | Purpose                 |
| --------------------------------- | ----------------------- |
| `app/page.tsx`                    | Market Overview landing |
| `app/chart/[symbol]/page.tsx`     | Chart view              |
| `components/CoinTable.tsx`        | Coins table             |
| `components/CandlestickChart.tsx` | TradingView chart       |
| `components/IndicatorToolbar.tsx` | Indicator management    |
| `stores/themeStore.ts`            | Dark/light mode         |
| `stores/indicatorStore.ts`        | Indicator state         |
| `lib/marketApi.ts`                | Market API client       |
| `hooks/useMarketOverview.ts`      | React Query hooks       |

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

1. Complete drawing tools (trendlines, fib retracements)
2. Watchlist/favorites feature
3. Portfolio tracking
