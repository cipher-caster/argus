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
- ✅ Dark/Light theme toggle
- ✅ Real-time price updates

### How to Run

```bash
# Terminal 1 - Backend
cd /home/mjm/Documents/argus/backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd /home/mjm/Documents/argus/frontend
npm run dev
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

1. Complete drawing tools (trendlines, fib retracements)
2. Separate pane indicators (RSI, MACD below chart)
3. Watchlist/favorites feature
4. Portfolio tracking
