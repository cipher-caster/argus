# Argus Codebase Guide for AI Agents

**Last Updated**: 2026-03-14
**Purpose**: Help AI agents quickly understand the Argus cryptocurrency analytics platform

---

## 🎯 What is Argus?

Argus is a **real-time cryptocurrency analytics dashboard** that provides:

- Market data visualization (OHLCV charts, tickers)
- Advanced technical indicators (RSI, MACD, structure analysis)
- AI-powered trading signals (Oracle Screener, Titan Radar)
- Market health monitoring
- Multi-timeframe analysis (1m to 1w)

**Tech Stack**:

- **Backend**: Python 3.11, FastAPI, PostgreSQL, Redis
- **Frontend**: Next.js 14, React, TanStack Query, TypeScript
- **Data Source**: Binance API (CCXT library)
- **Deployment**: Docker Compose

---

## 📁 Project Structure

```
argus/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── main.py       # FastAPI app entry point
│   │   ├── routes/       # API endpoints
│   │   ├── services/     # Business logic
│   │   ├── providers/    # External API wrappers (Binance)
│   │   ├── indicators/   # TA calculation modules
│   │   ├── strategies/   # Trading signal logic
│   │   ├── schemas/      # Pydantic models
│   │   ├── storage/      # Database & Redis clients
│   │   └── exceptions.py # Custom exception hierarchy
│   ├── tests/            # Pytest test suite
│   └── worker.py         # Background jobs (Redis cache sync)
├── frontend/             # Next.js frontend
│   ├── src/
│   │   ├── app/          # Next.js 14 App Router pages
│   │   ├── components/   # React components
│   │   ├── hooks/        # TanStack Query hooks
│   │   └── lib/          # API client, utilities
│   └── public/           # Static assets
├── docs/                 # Documentation (you are here!)
└── docker-compose.yml    # Development environment
```

---

## 🏗️ Architecture Overview

### Backend Architecture

**Data Flow**:

```
External API (Binance)
    ↓
Worker (background sync) → Redis Cache (30s-5min TTL)
    ↓                            ↓
PostgreSQL (historical) ← Routes/Services → Frontend
```

**Key Components**:

1. **Routes** (`app/routes/*.py`):
   - API endpoints (REST)
   - Input validation with Pydantic
   - Error handling with custom exceptions
   - Response models

2. **Services** (`app/services/*.py`):
   - Business logic layer
   - Data merging, filtering, sorting
   - Cache-aware data fetching

3. **Providers** (`app/providers/*.py`):
   - External API wrappers
   - `BinanceProvider`: CCXT wrapper for Binance
   - Handles rate limiting, retries

4. **Indicators** (`app/indicators/*.py`):
   - Technical analysis calculations
   - Uses pandas-ta for common indicators
   - Active: `screener.py`, `mean_reversion.py`

5. **Strategies** (`app/strategies/*.py`):
   - Trading signal generation
   - Combines multiple indicators
   - Example: `titan.py` - hybrid trend + momentum system

6. **Storage** (`app/storage/`):
   - `database.py`: PostgreSQL with sqlmodel
   - `redis_client.py`: Redis for caching

### Frontend Architecture

**Data Flow**:

```
Component → TanStack Query Hook → API Client → Backend
              ↓ (cache)
          Automatic refetch on stale
```

**Key Patterns**:

1. **TanStack Query** (React Query):
   - All server state managed by TanStack Query
   - Hooks in `hooks/` directory
   - Benefits: automatic caching, refetching, loading states

2. **Component Structure**:

   ```tsx
   // Standard pattern
   export function Component({ prop1, prop2 }) {
     // 1. Data fetching
     const { data, isLoading, error } = useDataHook();

     // 2. Event handlers
     const handleAction = () => {};

     // 3. Early returns (loading, error)
     if (isLoading) return <Skeleton />;
     if (error) return <Error />;

     // 4. Main render
     return <div>...</div>;
   }
   ```

3. **Lazy Loading**:
   - Heavy analytics components use Next.js `dynamic()`
   - Reduces initial bundle size
   - Example: `app/analytics/page.tsx`

---

## 🔑 Key Concepts

### 1. Caching Strategy

**Backend Cache (Redis)**:

- **Market tickers**: 30s TTL (fast, live prices)
- **Market snapshot**: 5min TTL (slow, rich metadata from CoinGecko)
- **Analytics results**: 360s TTL (expensive calculations — pre-warmed every 300s by worker)

**Frontend Cache (TanStack Query)**:

- **staleTime**: 60s–300s depending on endpoint (best-setups: 300s, screener: 120s, signal-summary: 60s)
- **gcTime**: 5min (how long cached data is kept)
- **refetchOnWindowFocus**: false (don't refetch when switching tabs)
- **keepPreviousData**: true (smooth transitions)

### 2. Error Handling

**Custom Exception Hierarchy**:

```python
ArgusException (base)
├── DataProviderError (Binance API issues) → 503
├── CacheError (Redis issues) → 500
├── CalculationError (TA calculation failures) → 500
└── ValidationError (invalid input) → 400
```

**Usage**:

```python
try:
    data = await provider.get_ohlcv(...)
except Exception as e:
    logger.error(f"Failed to fetch: {e}", exc_info=True)
    raise DataProviderError(f"Provider unavailable: {e}")
```

See: `docs/backend/ERROR_HANDLING.md` for detailed guide

### 3. Input Validation

**Shared Schemas** (`app/schemas/validation.py`):

- `SymbolValidator`: Ensures format like `BTC/USDT`
- `TimeframeValidator`: Allowed values: 1m, 5m, 15m, 1h, 4h, 1d, etc.
- `LimitValidator`: Range checks (1-1000)

**Usage in routes**:

```python
from app.schemas.validation import OHLCVRequest

@router.get("/ohlcv/{symbol}")
async def get_ohlcv(request: OHLCVRequest):
    # request.symbol, request.timeframe, request.limit are validated
    ...
```

---

## 📝 Coding Conventions

### Backend (Python)

1. **Docstrings**: Google-style

   ```python
   def function(arg1: str, arg2: int) -> dict:
       """
       Brief description.

       Detailed explanation of what the function does.

       Args:
           arg1: Description of arg1
           arg2: Description of arg2

       Returns:
           Description of return value

       Raises:
           ValueError: When validation fails
       """
   ```

2. **Logging**: Use `logger`, not `print()`

   ```python
   import logging
   logger = logging.getLogger(__name__)

   logger.info(f"Fetching {symbol} {timeframe}")
   logger.error(f"Failed: {e}", exc_info=True)
   ```

3. **Type Hints**: Always use type hints

   ```python
   from typing import List, Dict, Optional, Tuple

   async def fetch_data(symbol: str, limit: int = 100) -> List[Candle]:
       ...
   ```

### Frontend (TypeScript)

1. **No Debug Logs**: Remove all `console.log()` before production

2. **Type Safety**: Define interfaces for all data structures

   ```typescript
   interface CoinData {
     symbol: string;
     price: number;
     change_24h?: number;
   }
   ```

3. **Component Props**: Always define prop interfaces
   ```typescript
   interface ComponentProps {
     data: CoinData[];
     onSelect: (coin: CoinData) => void;
   }
   ```

---

## 🔧 Common Tasks

### Adding a New API Endpoint

1. **Define request/response models** in `app/schemas/`
2. **Create route** in `app/routes/`
   ```python
   @router.get("/new-endpoint")
   async def new_endpoint(param: str):
       try:
           result = await service.process(param)
           return {"data": result}
       except DataProviderError as e:
           raise HTTPException(status_code=503, detail=str(e))
   ```
3. **Add business logic** in `app/services/`
4. **Write tests** in `backend/tests/`
5. **Update frontend hook** in `frontend/src/hooks/`

### Adding a New Indicator

1. **Create function** in `app/indicators/`
   ```python
   def calculate_my_indicator(df: pd.DataFrame, period: int = 14) -> pd.Series:
       """
       Calculate custom indicator.

       Args:
           df: DataFrame with OHLCV data
           period: Calculation period

       Returns:
           Series with indicator values
       """
       # Calculation logic
       return result
   ```
2. **Add to indicator calculation** in `app/routes/indicators.py`
3. **Write tests**
4. **Update frontend visualization**

### Debugging Tips

1. **Check logs**: `docker compose logs backend -f`
2. **Redis data**: `docker compose exec redis redis-cli`
   ```
   keys *
   get market:tickers
   ```
3. **Database**: `docker compose exec db psql -U argus`
   ```sql
   SELECT * FROM candles LIMIT 10;
   ```
4. **Frontend console**: Open browser DevTools

---

## 🧪 Testing

**Backend**:

```bash
# Run all tests
docker compose exec backend pytest -v

# Run specific test file
docker compose exec backend pytest tests/test_analytics.py -v

# Run with coverage
docker compose exec backend pytest --cov=app tests/
```

**Frontend**:

```bash
cd frontend

# Type check
npx tsc --noEmit

# Build check
npm run build
```

---

## 📊 Recent Improvements (2026-03-14)

### v0.6.1 — Best Setups Enrichment + MTF Confluence

- ✅ Oracle backtest win rate surfaced on Best Setups cards (≥50% green, 33–49% yellow, <33% red; null when <10 trades)
- ✅ Eliz+Mayne MTF confluence: Titan signal confirmed on 4H/1D (Eliz) and 12H/1W (Mayne)
- ✅ 119 backend tests: oracle, titan, analytics, market, worker, screener

### v0.6.0 — Dashboard Redesign

- ✅ New dashboard layout: DashboardStatusBar, ActiveSetups, BTCCard, DashboardWatchlist, TopMovers
- ✅ /markets page for full CoinTable (freed dashboard from data overload)
- ✅ Space Grotesk + DM Mono fonts (self-hosted)
- ✅ DrawingToolbar removed — chart is now full-width
- ✅ CoinDetailsPanel shows Oracle + Titan signals

### v0.5.5 — Analytics Cleanup

- ✅ Removed Market Health, Trend Radar, Structure Scanner, Confluence Gauge, Liquidity Map (all redundant)
- ✅ Analytics streamlined from 7 tabs to 5

---

## 🤖 AI Slash Commands

Custom Claude Code slash commands live in `.claude/commands/`. These call the live Argus APIs and generate structured intelligence reports.

### `/read [COIN|market]`

```
/read BTC          # Coin deep-dive: price, Oracle, Titan, backtest, spot setup, key levels
/read ETH hold     # + Long-term HODL analysis with 12H/1D/1W macro stack and DCA plan
/read market       # Market overview: sentiment, screener, best setups, movers
```

See `docs/SLASH_COMMANDS.md` for full documentation including how to interpret every section of the report.

---

## 🚨 Important Notes for AI Agents

### When Making Changes

1. **Always run tests** after backend changes
2. **Check TypeScript compilation** after frontend changes
3. **Use existing patterns** - don't invent new ones
4. **Follow conventions** - docstrings, logging, validation
5. **Update documentation** when adding new features

### Current Limitations

1. **Indicators**: Not all indicator functions have docstrings yet
2. **Frontend**: No pagination on large tables (500+ items)
3. **Signal History**: No persistent log of fired signals yet

### Best Practices

1. **Error Handling**: Always use custom exceptions, never bare `Exception`
2. **Logging**: Include context (symbol, timeframe, counts) in log messages
3. **Validation**: Use Pydantic models for all API inputs
4. **Caching**: Be cache-aware - check Redis before hitting database/API
5. **Documentation**: Update this guide when architecture changes

---

## 📚 Key Files to Understand

**Must Read**:

1. `backend/app/main.py` - Application entry, router setup
2. `backend/app/exceptions.py` - Exception hierarchy
3. `backend/app/services/market_data.py` - Core data fetching logic
4. `frontend/src/hooks/useAnalyticsData.ts` - Query configuration
5. `docs/backend/ERROR_HANDLING.md` - Error handling guide

**Configuration**:

1. `docker-compose.yml` - Service definitions
2. `backend/.env` - Backend environment variables
3. `frontend/.env.local` - Frontend API URL

---

## 🔗 Useful Links

- **Backend API Docs**: http://localhost:8000/docs (FastAPI Swagger)
- **Frontend Dev**: http://localhost:3000
- **Redis CLI**: `docker compose exec redis redis-cli`
- **Database**: `docker compose exec db psql -U argus`

---

## 💡 Quick Start for AI Agents

**To understand the codebase**:

1. Read this document (you are here!)
2. Check `docs/backend/ERROR_HANDLING.md`
3. Review `backend/app/main.py` for route structure
4. Look at `backend/app/services/market_data.py` as an example of best practices

**To make changes**:

1. Identify the layer: routes → services → indicators → providers
2. Follow existing patterns in that layer
3. Add proper error handling with custom exceptions
4. Include docstrings and type hints
5. Write tests
6. Run tests before committing

**To debug issues**:

1. Check backend logs: `docker compose logs backend -f`
2. Verify Redis cache: `docker compose exec redis redis-cli`
3. Inspect database: `docker compose exec db psql -U argus`
4. Check frontend console in browser DevTools

---

**Remember**: This codebase values clarity, type safety, and production readiness. Always prefer explicit over implicit, documented over undocumented, and tested over untested.
