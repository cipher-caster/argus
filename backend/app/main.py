"""
Argus Crypto Dashboard - Backend API
FastAPI application for market data and analysis
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import market_router, indicators_router, strategy_router
from app.routes.analytics import router as analytics_router

from app.storage import Database

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    
    # Initialize Database (Storage)
    Database.init()
    print("✓ Argus Backend: Database initialized")

    # Initialize Data Provider
    from app.providers.binance_provider import BinanceProvider
    from app.routes.market import set_provider
    provider = BinanceProvider()
    set_provider(provider)
    print("✓ Argus Backend: Provider initialized")
    
    yield
    
    # Cleanup
    await provider.close()
    await Database.close()
    print("✓ Argus Backend: Storage closed")


app = FastAPI(
    title="Argus Crypto Dashboard API",
    description="High-performance trading interface backend",
    version="0.1.0",
    lifespan=lifespan
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(market_router)
app.include_router(indicators_router)
app.include_router(strategy_router)
app.include_router(analytics_router)



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "argus-backend"}

