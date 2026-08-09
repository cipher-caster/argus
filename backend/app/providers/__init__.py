"""
Data Providers Package
"""

from app.constants import active_provider_name

from .binance_provider import BinanceProvider
from .data_provider import Candle, DataProvider, SymbolInfo
from .okx_provider import OKXProvider

_shared: DataProvider | None = None


def set_shared_provider(provider: DataProvider) -> None:
    """Register the app-lifetime singleton provider (called once from lifespan)."""
    global _shared
    _shared = provider


def owns_provider(p: DataProvider) -> bool:
    """Return True if the caller created this provider and must close it.
    Returns False when p IS the shared singleton (owned by lifespan, not the caller)."""
    return p is not _shared


def provider_for(name: str) -> DataProvider:
    """Construct a provider instance by name. OKX is the canonical default;
    only an explicit "binance" selects Binance."""
    return BinanceProvider() if name == "binance" else OKXProvider()


def get_provider() -> DataProvider:
    """
    Return the shared provider singleton if one is registered (backend process),
    otherwise create a new instance (worker process, tests).
    """
    if _shared is not None:
        return _shared
    return provider_for(active_provider_name())


__all__ = [
    "DataProvider",
    "Candle",
    "SymbolInfo",
    "BinanceProvider",
    "OKXProvider",
    "provider_for",
    "get_provider",
    "set_shared_provider",
    "owns_provider",
]
