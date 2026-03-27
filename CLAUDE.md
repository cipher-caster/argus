# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Argus is a cryptocurrency analytics dashboard — real-time market data, technical indicators, and AI-powered trading signals for 400+ pairs from Binance.

## Commands

### Docker (Primary Development)

```bash
docker-compose up -d               # Start all services
docker-compose up -d --build       # Start with rebuild (after code changes)
docker-compose down                # Stop all services
docker-compose logs -f backend     # Stream backend logs
docker-compose logs -f worker      # Stream worker logs
```

### Backend (Python/FastAPI)

```bash
# Run tests
docker compose exec backend pytest
docker compose exec backend pytest -v
docker compose exec backend pytest --cov=app tests/
docker compose exec backend pytest tests/test_specific.py::test_name  # Single test

# Start locally (outside Docker)
cd backend && uvicorn app.main:app --reload
```

### Frontend (Next.js)

```bash
cd frontend
npm run dev          # Development server
npm run build        # Production build
npm start            # Serve production build
npx tsc --noEmit    # Type check
npx playwright test  # E2E tests
```

### Database Access

```bash
docker compose exec db psql -U argus
docker compose exec redis redis-cli
```

## Architecture

**Services (docker-compose):** frontend (3000) → backend (8000) → Redis (6379) + PostgreSQL (5433). A separate `worker` service runs background jobs via arq.

**Data flow:**
1. Frontend calls FastAPI REST endpoints
2. FastAPI checks Redis cache (30–180s TTL), falls back to PostgreSQL
3. Worker background jobs fetch from Binance via CCXT, populate Redis/Postgres

**Backend layers** (`backend/app/`):
- `routes/` — FastAPI route handlers with input validation (`strategy.py` for regime endpoint)
- `services/` — Business logic, cache coordination (`market_data.py`)
- `indicators/` — Technical analysis (pandas-ta): `screener.py`, `mean_reversion.py`
- `strategies/` — Trading signal generation: `oracle.py` (deprecated from UI, backend preserved), `titan.py` (hybrid trend-momentum, primary strategy)
- `jobs/` — Worker background jobs: `signal_log.py` (scan watchlist at 4H candle close with regime-based filtering, resolve outcomes every 30min)
- `trading/` — Paper trading engine: orchestrator, risk manager, portfolio, backtest engine, optimizer
- `providers/` — CCXT Binance wrapper (`binance_provider.py`)
- `schemas/` — Pydantic v2 models
- `storage.py` — Redis + Postgres connection pooling
- `exceptions.py` — Custom exception hierarchy (`ArgusException` → `DataProviderError` / `CacheError` / `CalculationError` / `ValidationError`)

**Frontend layers** (`frontend/src/`):
- `app/` — Next.js 14 App Router pages (`/`, `/chart/[symbol]`, `/markets/[type]`, `/analytics`)
- `components/features/` — Feature components (dashboard, chart). Chart sidebar: `CoinDetailsPanel` (price/regime/Titan), `CoinSignalIntel` (backtest stats + open signals), `CoinAnalysisModal` (deep analysis with signal track record)
- `components/analytics/` — Analytics panels: `BestSetups`, `SignalLog`, `BacktestPerformance`
- `components/features/dashboard/` — Dashboard widgets: `BestSetups`, `BTCCard`, `DashboardWatchlist`, `TopMovers`, `DashboardStatusBar` (regime display + modal)
- `components/ui/` — Shadcn UI primitives
- `hooks/` — TanStack Query v5 custom hooks (staleTime varies: 60s–300s, gcTime 5min)
- `stores/` — Zustand stores (theme, indicators, watchlist, chart settings)
- `lib/` — API client factory and per-domain API functions

## Key Conventions

- **Error handling:** Raise from the `exceptions.py` hierarchy — `DataProviderError` → 503, `ValidationError` → 400, `CacheError`/`CalculationError` → 500.
- **Type safety:** Strict TypeScript on the frontend; type hints on all Python functions with Pydantic validation at API boundaries.
- **Caching:** Always check Redis before hitting Binance. Cache keys and TTLs are managed in `services/market_data.py`.
- **API docs:** Swagger UI available at `http://localhost:8000/docs` during development.
- **Key endpoint:** `GET /api/strategy/regime` — BTC weekly EMA50 regime detection.

## Documentation

Detailed architecture and implementation docs live in `docs/`:
- `docs/AI_AGENT_GUIDE.md` — Extended codebase overview
- `docs/backend/ARCHITECTURE.md` — Backend system design
- `docs/frontend/ARCHITECTURE.md` — Frontend patterns
- `docs/backend/ERROR_HANDLING.md` — Exception hierarchy details
- `docs/CHANGELOG.md` — Version history (current: v0.9.4)
- `docs/ROADMAP.md` — Planned features

## AI Slash Commands

Custom Claude Code commands live in `.claude/commands/`:

### `/read [COIN|market]`

Calls the live Argus APIs and produces a structured intelligence report.

```
/read BTC          # Deep-dive: price, regime + Titan signal, backtest stats
/read market       # Market overview: sentiment, screener highlights, best setups, movers
/read              # Alias for /read market
```

Requires the backend to be running (`http://localhost:8000`). If it's down, start it with `docker-compose up -d`.

### `/portfolio`

Calls the Argus trading API and produces a portfolio intelligence report — positions, P&L, drawdown, balance.

### `/trade`

Calls the Argus trading API and produces a trade management report — enable/disable trading, view config, recent events.

### `/optimize [sweep|analyze|apply|status]`

Run a trading optimization loop — parameter sweeps, backtest analysis, apply best config to production.

```
/optimize sweep sl_sweep    # Run SL multiplier sweep
/optimize analyze           # Compare backtest vs live performance
/optimize apply             # Apply best experiment config to production
/optimize status            # Show current production config vs best experiment
```

### `/review [trading|docs|plan]`

Full system review — trading pipeline health, documentation freshness, memory audit, and next-step planning.

```
/review              # Full review: trading state, docs, memory, plan
/review trading      # Signal pipeline and paper trading health only
/review docs         # Documentation staleness check only
/review plan         # Skip review, jump to planning next steps
```

### `/backtest`

Runs a signal backtest across the watchlist using the configured Titan strategy.

```
/backtest
```

### `/test-phase-a`

Runs Phase A backend safety net tests (backtest engine, outcome resolution, TradeAnalyzer).

### `/test-phase-b`

Runs Phase B frontend E2E expansion tests (data rendering, trading page).

### `/test-phase-c`

Runs Phase C trading analytics integration tests (signal log joins, regime capture).
