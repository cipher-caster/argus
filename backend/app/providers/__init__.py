"""
Data Providers Package
"""

import os
from typing import Optional
from .data_provider import DataProvider, Candle, SymbolInfo
from .binance_provider import BinanceProvider
from .okx_provider import OKXProvider


_shared: Optional[DataProvider] = None


def set_shared_provider(provider: DataProvider) -> None:
    """Register the app-lifetime singleton provider (called once from lifespan)."""
    global _shared
    _shared = provider


def owns_provider(p: DataProvider) -> bool:
    """Return True if the caller created this provider and must close it.
    Returns False when p IS the shared singleton (owned by lifespan, not the caller)."""
    return p is not _shared


def get_provider() -> DataProvider:
    """
    Return the shared provider singleton if one is registered (backend process),
    otherwise create a new instance (worker process, tests).
    """
    if _shared is not None:
        return _shared
    name = os.getenv("DATA_PROVIDER", "binance").lower()
    if name == "okx":
        return OKXProvider()
    return BinanceProvider()


__all__ = [
    'DataProvider',
    'Candle',
    'SymbolInfo',
    'BinanceProvider',
    'OKXProvider',
    'get_provider',
    'set_shared_provider',
    'owns_provider',
]
