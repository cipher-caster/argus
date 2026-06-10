"""
Argus Crypto Dashboard - Backend API
FastAPI application for market data and analysis
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import indicators_router, market_router, strategy_router
from app.routes.analytics import router as analytics_router
from app.routes.optimization import analysis_router
from app.routes.optimization import router as optimization_router
from app.routes.system import router as system_router
from app.routes.trading import router as trading_router
from app.storage import Database

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""

    # Initialize Database
    try:
        Database.init()
        print("✓ Argus Backend: Database initialized")
    except Exception as e:
        print(f"✗ Argus Backend: Database init failed — {e}")
        raise RuntimeError(f"Database initialization failed: {e}") from e

    # Initialize Data Provider
    try:
        from app.providers import get_provider, set_shared_provider
        from app.routes.market import set_provider

        provider = get_provider()
        set_shared_provider(provider)
        set_provider(provider)
        print("✓ Argus Backend: Provider initialized")
    except Exception as e:
        print(f"✗ Argus Backend: Provider init failed — {e}")
        raise RuntimeError(f"Provider initialization failed: {e}") from e

    yield

    # Cleanup
    try:
        await provider.close()
    except Exception as e:
        print(f"Warning: provider close failed — {e}")
    await Database.close()
    print("✓ Argus Backend: Storage closed")


app = FastAPI(
    title="Argus Crypto Dashboard API",
    description="High-performance trading interface backend",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# Include routers
app.include_router(market_router)
app.include_router(indicators_router)
app.include_router(strategy_router)
app.include_router(analytics_router)
app.include_router(trading_router)
app.include_router(optimization_router)
app.include_router(analysis_router)
app.include_router(system_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.storage import Database, RedisClient

    checks = {"service": "argus-backend", "database": "ok", "redis": "ok"}
    try:
        r = RedisClient.get_instance()
        await r.ping()
    except Exception:
        checks["redis"] = "unavailable"
    if Database._engine is None:
        checks["database"] = "unavailable"
    status = (
        "healthy" if all(v == "ok" for k, v in checks.items() if k != "service") else "degraded"
    )
    checks["status"] = status
    from fastapi.responses import JSONResponse

    code = 200 if status == "healthy" else 503
    return JSONResponse(content=checks, status_code=code)
