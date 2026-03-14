# Argus

Cryptocurrency analytics dashboard — real-time market data, technical indicators, and AI-powered trading signals for 400+ pairs from Binance.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router), TanStack Query v5, Shadcn UI, Zustand |
| Backend | FastAPI, Python 3.11, pandas-ta |
| Database | PostgreSQL (candles), Redis (cache) |
| Worker | ARQ (async jobs), CCXT Binance, CoinGecko |

## Quick Start

```bash
docker-compose up -d --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |

## Features

- **Dashboard** — Live prices, market summary, signal overview, best setups
- **Oracle Screener** — Prophet v9.0 scoring (-4 to +4) across top 50 coins
- **Best Setups** — Oracle + Titan confluence with backtest win rate and Eliz+Mayne MTF confirmation
- **Titan Signals** — Hybrid trend-momentum scanner with limit entry detection
- **Contrarian Radar** — ATR mean-reversion opportunities
- **Chart** — Interactive OHLCV chart with EMA, SMA, RSI, MACD, Bollinger Bands

## Signals

### Oracle (Prophet v9.0)
Earnest Brain scores 4 indicators (RSI, BB, ADX, EMA) on the micro timeframe, filtered by a macro trend check on the daily. Score range: -4 (strong sell) to +4 (strong buy).

### Titan
Hybrid trend + momentum strategy. Signals: `BUY`, `SELL`, `BUY_LIMIT`, `SELL_LIMIT`, `WAIT_OB`, `WAIT_OS`. Limit signals include a specific entry price based on EMA20/SuperTrend levels.

### Best Setups
Oracle and Titan confluence scored 0–100. Includes:
- Oracle backtest win rate (break-even = 33.3% at 2:1 RR)
- Eliz+Mayne MTF confirmation: 4H (entry), 1D (structure), 12H (bias), 1W (macro)

## Project Structure

```
argus/
├── backend/           # FastAPI app
│   └── app/
│       ├── routes/    # API endpoints
│       ├── services/  # Business logic + cache
│       ├── indicators/# Technical analysis (pandas-ta)
│       ├── strategies/# Oracle + Titan signal generation
│       ├── schemas/   # Pydantic v2 models
│       └── worker.py  # ARQ background jobs
├── frontend/          # Next.js app
│   └── src/
│       ├── app/       # Pages (App Router)
│       ├── components/# UI + feature components
│       ├── hooks/     # TanStack Query hooks
│       ├── stores/    # Zustand state
│       └── lib/       # API client + utilities
├── docs/              # Architecture + API docs
└── .claude/commands/  # Claude Code AI slash commands
```

## Tests

```bash
# Backend
docker compose exec backend pytest
docker compose exec backend pytest --cov=app tests/

# Frontend
cd frontend && npx tsc --noEmit   # type check
cd frontend && npx playwright test # E2E
```

## AI Commands (Claude Code)

Custom slash commands in `.claude/commands/` extend Claude Code for this project:

### `/read [COIN|market]`

Fetches live data from the Argus API and generates a structured intelligence report.

```
/read BTC          # Price, Oracle signal, Titan signal, backtest performance
/read SOL 4h       # Same with 4h Oracle micro timeframe
/read market       # Market sentiment, top signals, best setups, movers
/read              # Alias for /read market
```

Requires the backend to be running. If it's offline: `docker-compose up -d`

## Docs

- [`docs/AI_AGENT_GUIDE.md`](docs/AI_AGENT_GUIDE.md) — Full codebase guide for AI agents
- [`docs/backend/API.md`](docs/backend/API.md) — REST API reference
- [`docs/backend/ARCHITECTURE.md`](docs/backend/ARCHITECTURE.md) — Backend design
- [`docs/frontend/ARCHITECTURE.md`](docs/frontend/ARCHITECTURE.md) — Frontend patterns
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — Version history
