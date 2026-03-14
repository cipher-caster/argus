# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Argus is a cryptocurrency analytics dashboard — real-time market data, technical indicators, and AI-powered trading signals for 400+ pairs from Binance.

## Commands

### Docker (Primary Development)

```bash
docker-compose up -d --build       # Start all services
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
- `routes/` — FastAPI route handlers with input validation
- `services/` — Business logic, cache coordination (`market_data.py`)
- `indicators/` — Technical analysis (pandas-ta): `screener.py`, `relative_strength.py`, `mean_reversion.py`
- `strategies/` — Trading signal generation: `oracle.py` (Earnest + Prophet), `titan.py` (hybrid trend-momentum)
- `providers/` — CCXT Binance wrapper (`binance_provider.py`)
- `schemas/` — Pydantic v2 models
- `storage.py` — Redis + Postgres connection pooling
- `exceptions.py` — Custom exception hierarchy (`ArgusException` → `DataProviderError` / `CacheError` / `CalculationError` / `ValidationError`)

**Frontend layers** (`frontend/src/`):
- `app/` — Next.js 14 App Router pages (`/`, `/chart/[symbol]`, `/markets/[type]`, `/analytics`)
- `components/features/` — Feature components (dashboard, chart)
- `components/analytics/` — Analytics panels: `OracleScreener`, `TitanRadar`, `TitanSignalsPanel`, `ContrarianRadar`, `RelativeStrength`
- `components/ui/` — Shadcn UI primitives
- `hooks/` — TanStack Query v5 custom hooks (cache: 120s staleTime, 5min gcTime)
- `stores/` — Zustand stores (theme, indicators, watchlist, chart settings)
- `lib/` — API client factory and per-domain API functions

## Key Conventions

- **Error handling:** Raise from the `exceptions.py` hierarchy — `DataProviderError` → 503, `ValidationError` → 400, `CacheError`/`CalculationError` → 500.
- **Type safety:** Strict TypeScript on the frontend; type hints on all Python functions with Pydantic validation at API boundaries.
- **Caching:** Always check Redis before hitting Binance. Cache keys and TTLs are managed in `services/market_data.py`.
- **API docs:** Swagger UI available at `http://localhost:8000/docs` during development.

## Documentation

Detailed architecture and implementation docs live in `docs/`:
- `docs/AI_AGENT_GUIDE.md` — Extended codebase overview
- `docs/backend/ARCHITECTURE.md` — Backend system design
- `docs/frontend/ARCHITECTURE.md` — Frontend patterns
- `docs/backend/ERROR_HANDLING.md` — Exception hierarchy details
- `docs/CHANGELOG.md` — Version history (current: v0.5.4)
- `docs/ROADMAP.md` — Planned features
