# Argus

Cryptocurrency analytics dashboard — real-time market data, technical indicators, and AI-powered trading signals for 400+ pairs from Binance.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router), TanStack Query v5, Shadcn UI, Zustand |
| Backend | FastAPI, Python 3.11, pandas-ta |
| Database | PostgreSQL (candles, signals, positions, experiments), Redis (cache) |
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

- **Dashboard** — Regime status bar, best setups, BTC card, watchlist, top movers
- **Markets** — Full 400-coin table with sort, pagination, sparklines
- **Chart** — Interactive OHLCV chart with EMA, SMA, RSI, MACD, Bollinger Bands + Titan signal panel
- **Best Setups** — Titan signals filtered by BTC weekly EMA50 regime (BULL→LONG, BEAR→SHORT)
- **Signal Log** — Forward-test track record: live/scanner signals with WIN/LOSS/REVIEW outcomes
- **Paper Trading** — Full simulation engine: signal → position lifecycle, risk manager, portfolio tracking
- **Trading Page** — Positions, trade history, equity curve, risk settings
- **Optimization** — Parameter sweeps, backtest vs live analysis, experiment tracking

## Signal Pipeline

### Regime Detection
BTC weekly EMA50 determines market regime: BULL (price > EMA50), BEAR (price < EMA50). Signals are filtered by regime — BULL allows LONG only, BEAR allows SHORT only.

### Titan
Hybrid trend + momentum strategy. Signals: `BUY`, `SELL`, `BUY_LIMIT`, `SELL_LIMIT`, `WAIT_OB`, `WAIT_OS`. Per-symbol risk overrides (BTC: SL=1.75x ATR, TP=4.0x ATR; ETH: TP=4.0x ATR).

### Signal Resolution
Outcomes resolved via 4H candle walk. When both TP and SL hit in the same candle, 5min candles determine exact ordering. Falls back to conservative LOSS if 5min data unavailable.

## Project Structure

```
argus/
├── backend/             # FastAPI app
│   └── app/
│       ├── routes/      # API endpoints
│       ├── services/    # Business logic + cache
│       ├── indicators/  # Technical analysis (pandas-ta)
│       ├── strategies/  # Titan signal generation
│       ├── trading/     # Paper trading engine
│       │   ├── orchestrator.py  # Signal → position lifecycle
│       │   ├── risk_manager.py  # Risk gates
│       │   ├── portfolio.py     # P&L tracking
│       │   ├── backtest_engine.py  # Reusable backtest core
│       │   └── analyzer.py      # Live vs backtest comparison
│       ├── jobs/        # Worker background jobs
│       ├── schemas/     # Pydantic v2 + SQLModel tables
│       ├── providers/   # CCXT Binance wrapper
│       └── worker.py    # ARQ background job scheduler
├── frontend/            # Next.js app
│   └── src/
│       ├── app/         # Pages: /, /chart/[symbol], /markets, /trading, /analytics
│       ├── components/  # UI + feature components
│       ├── hooks/       # TanStack Query hooks
│       ├── stores/      # Zustand state (theme, indicators, watchlist, chart)
│       └── lib/         # API client + formatters + utilities
├── docs/                # Architecture + API docs
└── .claude/commands/    # Claude Code AI slash commands
```

## Tests

254 backend tests, 18+ frontend E2E tests.

```bash
# Backend
docker compose exec backend pytest -v

# Frontend
cd frontend && npx tsc --noEmit   # type check
cd frontend && npx playwright test # E2E
```

## AI Commands (Claude Code)

Custom slash commands in `.claude/commands/`:

```
/read BTC          # Price, regime + Titan signal, backtest stats
/read market       # Market sentiment, best setups, movers
/portfolio         # Portfolio intelligence: positions, P&L, drawdown
/trade             # Trade management: enable/disable, config, recent events
/optimize sweep    # Run parameter sweep
/optimize analyze  # Compare backtest vs live performance
/review            # Full system review: trading state, docs, plan
```

Requires the backend to be running. If it's offline: `docker-compose up -d`

## Docs

- [`CLAUDE.md`](CLAUDE.md) — AI agent instructions and architecture overview
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — Version history (current: v0.9.3)
- [`docs/AI_AGENT_GUIDE.md`](docs/AI_AGENT_GUIDE.md) — Full codebase guide
- [`docs/backend/ARCHITECTURE.md`](docs/backend/ARCHITECTURE.md) — Backend design + worker schedule
- [`docs/strategies/OVERVIEW.md`](docs/strategies/OVERVIEW.md) — Strategy reference
