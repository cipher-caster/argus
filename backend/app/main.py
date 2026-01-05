"""
Magus Crypto Dashboard - Backend API
FastAPI application for market data and analysis
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import market_router, indicators_router, set_provider
from app.providers import BinanceProvider, OKXProvider


load_dotenv()

# Active provider instance
_provider = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage provider lifecycle"""
    global _provider
    
    # Get provider from environment (default to binance)
    provider_name = os.getenv("DATA_PROVIDER", "binance").lower()
    
    if provider_name == "okx":
        _provider = OKXProvider()
    else:
        _provider = BinanceProvider()
    
    # Set provider for routes
    set_provider(_provider)
    
    print(f"✓ Magus Backend started with {_provider.name} provider")
    
    yield
    
    # Cleanup
    if _provider:
        await _provider.close()
        print("✓ Provider connection closed")


app = FastAPI(
    title="Magus Crypto Dashboard API",
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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "magus-backend"}
