# Argus

A professional cryptocurrency dashboard for real-time market data, charting, and technical analysis.

## Features

- **Market Overview** - CoinGecko-style dashboard with 400+ coins
- **Interactive Charts** - TradingView-powered candlestick charts
- **Technical Indicators** - EMA, SMA, Bollinger Bands, RSI, MACD, and more
- **Dark/Light Theme** - Toggle between themes
- **Real-time Data** - Live prices from Binance

## Tech Stack

| Layer    | Technology                     |
| -------- | ------------------------------ |
| Frontend | Next.js 14, React, TypeScript  |
| State    | Zustand, React Query           |
| Charts   | TradingView Lightweight Charts |
| Backend  | FastAPI, Python                |
| Data     | CCXT (Binance, OKX)            |

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

See the [docs/](./docs/) folder for:

- [Architecture](./docs/ARCHITECTURE.md)
- [Roadmap](./docs/ROADMAP.md)

## License

MIT
