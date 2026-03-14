"""
Data Providers Package
"""

import os
from .data_provider import DataProvider, Candle, SymbolInfo
from .binance_provider import BinanceProvider
from .okx_provider import OKXProvider


def get_provider() -> DataProvider:
    """
    Factory that returns a provider instance based on the DATA_PROVIDER env var.
    Supported values: 'binance' (default), 'okx'
    """
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
]
