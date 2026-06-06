# Argus

Cryptocurrency analytics dashboard — real-time market data, technical indicators, and AI-powered trading signals for 400+ pairs. Market and execution data flow through CCXT (OKX by default); the paper-trading engine uses OKX as the canonical venue.

> ⚠️ **Not financial advice.** Argus is an experimental, educational project for testing
> trading setups and configurations — it ships a **paper-trading** engine, not a live broker.
> Signals, backtests, and "best setups" are research outputs, not recommendations. Crypto
> trading is high-risk and you can lose money. Use this software entirely at your own risk;
> see the [Disclaimer](#disclaimer) for the full terms.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 (App Router), TanStack Query v5, Shadcn UI, Zustand |
| Backend | FastAPI, Python 3.11, pandas-ta |
| Database | PostgreSQL (candles, signals, positions, experiments), Redis (cache) |
| Worker | ARQ (async jobs), CCXT (OKX by default), CoinGecko |

## Quick Start

```bash
cp .env.example .env        # optional — defaults work out of the box
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
Hybrid trend + momentum strategy built on ADX(14). Signals: `BUY`, `SELL`, `BUY_LIMIT`, `SELL_LIMIT`, `WAIT_OB`, `WAIT_OS`. Stops and targets are derived from ATR.

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
│       ├── providers/   # CCXT exchange wrapper
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

## Configuration

Copy `.env.example` to `.env` and adjust as needed. The defaults work out of the box
with the bundled Docker Compose stack.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` / `POSTGRES_*` | PostgreSQL connection (candles, signals, positions) |
| `REDIS_URL` | Redis cache connection |
| `DATA_PROVIDER` | Exchange for CCXT market/execution data (default: `okx`) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Optional signal alerts |

> **Note:** Market-cap and metadata sync uses the free, unauthenticated CoinGecko API,
> which is rate-limited (~10–30 calls/min). The worker self-throttles to stay within it.
> For heavier use, add a CoinGecko Pro API key (not currently wired up).

## Tests

Comprehensive backend unit/integration suite (pytest) and Playwright E2E tests.

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
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — Version history (current: v1.1.4)
- [`docs/AI_AGENT_GUIDE.md`](docs/AI_AGENT_GUIDE.md) — Full codebase guide
- [`docs/backend/ARCHITECTURE.md`](docs/backend/ARCHITECTURE.md) — Backend design + worker schedule
- [`docs/strategies/OVERVIEW.md`](docs/strategies/OVERVIEW.md) — Strategy reference

## Disclaimer

This software is provided **for educational and research purposes only**. It is **not
financial, investment, or trading advice**, and nothing it produces should be construed as a
recommendation to buy, sell, or hold any asset.

- Argus is an **experimental tool** for testing strategies, setups, and configurable parameters.
  The trading engine is **paper-trading only** — it simulates orders and does not execute real
  trades or move real funds.
- Backtests and historical results **do not guarantee future performance**. Markets change;
  signals that worked before may fail.
- Cryptocurrency trading carries a **high level of risk** and can result in the loss of some or
  all of your capital. Only risk what you can afford to lose.
- You are **solely responsible** for any decisions you make and any trades you place with real
  funds. The author and contributors accept **no liability** for any losses or damages arising
  from the use of this software.

By using Argus you acknowledge that you do so **entirely at your own risk**. The software is
provided "as is", without warranty of any kind — see [`LICENSE`](LICENSE) for the full terms.
