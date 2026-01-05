# Architecture

## Overview

Argus is a full-stack cryptocurrency dashboard built with a Python backend and React frontend.

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  Next.js 14 + React + TypeScript                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Market      │ │ Chart       │ │ Indicators  │           │
│  │ Overview    │ │ View        │ │ System      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│                         │                                    │
│              ┌──────────┴──────────┐                        │
│              │ React Query + Zustand│                        │
│              └──────────┬──────────┘                        │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTP/REST
┌─────────────────────────┼───────────────────────────────────┐
│                         ▼                                    │
│                    FastAPI Backend                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Market      │ │ OHLCV       │ │ Indicators  │           │
│  │ Routes      │ │ Routes      │ │ Calculator  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│                         │                                    │
│              ┌──────────┴──────────┐                        │
│              │   Data Providers     │                        │
│              │  (CCXT: Binance/OKX) │                        │
│              └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Backend

### Providers

- `BinanceProvider` - Primary exchange using CCXT
- `OKXProvider` - Alternative exchange support
- Extensible for adding more exchanges

### Routes

| Endpoint                         | Description             |
| -------------------------------- | ----------------------- |
| `GET /api/ohlcv/{symbol}`        | Candlestick data        |
| `GET /api/symbols`               | Available trading pairs |
| `GET /api/ticker/{symbol}`       | Current price           |
| `GET /api/market/coins`          | Paginated coin list     |
| `POST /api/indicators/calculate` | Technical indicators    |

### Indicators

Powered by `pandas-ta`:

- Overlay: EMA, SMA, Bollinger Bands, Linear Regression
- Oscillators: RSI, MACD, OBV

## Frontend

### State Management

- **Zustand** - Global stores for indicators, theme, drawings
- **React Query** - Server state caching and refetching

### Key Components

- `CandlestickChart` - TradingView chart wrapper
- `CoinTable` - Market overview table
- `IndicatorToolbar` - Indicator management
- `ThemeToggle` - Dark/light mode

### Routing

| Route             | Component       |
| ----------------- | --------------- |
| `/`               | Market Overview |
| `/chart/[symbol]` | Chart View      |
