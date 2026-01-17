# Argus

A professional cryptocurrency dashboard for real-time market data, charting, and technical analysis.

## Features

- **Market Overview** - CoinGecko-style dashboard with 400+ coins
- **Analytics Dashboard** - Charts for Funding Rates, Open Interest, and Long/Short Ratios
- **Argus Oracle** - Professional trading strategies (Earnest & Prophet) with live backtesting
- **Strategy Performance** - Real-time Win Rate and Net PnL tracking for active strategies
- **Liquidation Heatmap** - Real-time visualization of market liquidations
- **Interactive Charts** - TradingView-powered candlestick charts with Refresh capability
- **Technical Indicators** - EMA, SMA, Bollinger Bands, RSI, MACD, and more
- **Dark/Light Theme** - Toggle between themes
- **Real-time Data** - Live prices from Binance

## Tech Stack

| Layer    | Technology                               |
| -------- | ---------------------------------------- |
| Frontend | Next.js 14, React, Tailwind, Shadcn UI   |
| State    | Zustand, React Query                     |
| Charts   | TradingView Lightweight Charts, Chart.js |
| Backend  | FastAPI, Python, Websockets              |
| Data     | CCXT (Binance), Redis, Postgres          |

## Quick Start

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend Unit Tests
docker compose exec backend sh -c "export PYTHONPATH=$PYTHONPATH:/app && pytest"

# Frontend E2E Tests
cd frontend && npx playwright test
```

- **App**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## Project Structure

```
argus/
├── backend/           # FastAPI server
│   ├── app/
│   │   ├── providers/ # Exchange data providers
│   │   ├── routes/    # API endpoints
│   │   └── indicators/# Technical indicators
│   └── requirements.txt
├── frontend/          # Next.js app
│   ├── src/
│   │   ├── app/       # Pages
│   │   ├── components/# React components
│   │   ├── hooks/     # Custom hooks
│   │   ├── lib/       # API clients
│   │   └── stores/    # Zustand stores
│   └── package.json
└── docs/              # Documentation
```

## Documentation

For detailed technical documentation, architecture diagrams, and the project roadmap, please see the **[Documentation Hub](./docs/README.md)**.

## License

MIT
