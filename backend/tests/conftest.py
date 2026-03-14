"""
Shared test fixtures and helpers for the backend test suite.
"""
import pytest
import pytest_asyncio
import numpy as np
import pandas as pd
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


# ---------------------------------------------------------------------------
# HTTP client fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# ---------------------------------------------------------------------------
# OHLCV data generators
# ---------------------------------------------------------------------------

def make_ohlcv(
    n: int = 300,
    base_price: float = 100.0,
    trend: str = "up",
    freq: str = "1h",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic OHLCV DataFrame with a clear trend.

    Parameters:
        n: number of candles
        base_price: starting price
        trend: 'up' or 'down'
        freq: pandas frequency string
        seed: random seed for reproducibility
    """
    np.random.seed(seed)
    prices = [base_price]
    for _ in range(n - 1):
        delta = np.random.normal(0.1 if trend == "up" else -0.1, 0.5)
        prices.append(max(1.0, prices[-1] + delta))

    prices = np.array(prices)
    high = prices * np.random.uniform(1.001, 1.01, n)
    low = prices * np.random.uniform(0.99, 0.999, n)
    volume = np.random.uniform(1000, 5000, n)

    timestamps = pd.date_range("2024-01-01", periods=n, freq=freq)
    return pd.DataFrame({
        "timestamp": timestamps,
        "open": prices,
        "high": high,
        "low": low,
        "close": prices,
        "volume": volume,
    })


def make_bullish_ohlcv(n: int = 250, seed: int = 1) -> pd.DataFrame:
    """Strong uptrend — price ramps from 50 to 200, ending well above EMA200."""
    np.random.seed(seed)
    prices = np.linspace(50, 200, n) + np.random.normal(0, 0.5, n)
    prices = np.clip(prices, 1, None)
    high = prices * 1.005
    low = prices * 0.995
    volume = np.random.uniform(2000, 8000, n)
    timestamps = pd.date_range("2024-01-01", periods=n, freq="4h")
    return pd.DataFrame({
        "timestamp": timestamps,
        "open": prices,
        "high": high,
        "low": low,
        "close": prices,
        "volume": volume,
    })


def make_bearish_ohlcv(n: int = 250, seed: int = 2) -> pd.DataFrame:
    """Strong downtrend — price ramps from 200 to 50, ending well below EMA200."""
    np.random.seed(seed)
    prices = np.linspace(200, 50, n) + np.random.normal(0, 0.5, n)
    prices = np.clip(prices, 1, None)
    high = prices * 1.005
    low = prices * 0.995
    volume = np.random.uniform(2000, 8000, n)
    timestamps = pd.date_range("2024-01-01", periods=n, freq="4h")
    return pd.DataFrame({
        "timestamp": timestamps,
        "open": prices,
        "high": high,
        "low": low,
        "close": prices,
        "volume": volume,
    })


# ---------------------------------------------------------------------------
# Mock cache helpers
# ---------------------------------------------------------------------------

def mock_cache_miss():
    """Returns a mock Redis client that always misses cache."""
    mock = AsyncMock()
    mock.get_json = AsyncMock(return_value=None)
    mock.set_json = AsyncMock(return_value=True)
    return mock


def mock_cache_hit(data):
    """Returns a mock Redis client that always hits with given data."""
    mock = AsyncMock()
    mock.get_json = AsyncMock(return_value=data)
    mock.set_json = AsyncMock(return_value=True)
    return mock


# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

MOCK_SCREENER_DATA = [
    {"symbol": "BTCUSDT", "price": 50000.0, "score": 3, "confidence": "3/4",
     "bias": "BULLISH", "state": "TRENDING", "liquidity": "ACTIVE",
     "strength_vs_btc": "STRONG", "opportunity": "LONG", "advice": "Strong buy setup"},
    {"symbol": "ETHUSDT", "price": 3000.0, "score": -3, "confidence": "3/4",
     "bias": "BEARISH", "state": "TRENDING", "liquidity": "ACTIVE",
     "strength_vs_btc": "WEAK", "opportunity": "SHORT", "advice": "Strong sell setup"},
    {"symbol": "SOLUSDT", "price": 100.0, "score": 1, "confidence": "1/4",
     "bias": "BULLISH", "state": "SLEEPING", "liquidity": "ACTIVE",
     "strength_vs_btc": "NEUTRAL", "opportunity": "NONE", "advice": "Wait"},
    {"symbol": "BNBUSDT", "price": 300.0, "score": 0, "confidence": "0/4",
     "bias": "NEUTRAL", "state": "SLEEPING", "liquidity": "ACTIVE",
     "strength_vs_btc": "NEUTRAL", "opportunity": "NONE", "advice": "No signal"},
]

MOCK_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

VALID_MARKET_STATES = {"STRONG BULL", "STRONG BEAR", "NEUTRAL", "SLEEPING"}
