"""
Data Provider Abstraction Layer
Defines the interface for all market data sources (Binance, OKX, CoinGecko)
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class Candle(BaseModel):
    """OHLCV candlestick data"""

    timestamp: int  # Unix timestamp in milliseconds
    open: float
    high: float
    low: float
    close: float
    volume: float


class SymbolInfo(BaseModel):
    """Trading pair information"""

    symbol: str  # e.g., "BTC/USDT"
    base: str  # e.g., "BTC"
    quote: str  # e.g., "USDT"


class DataProvider(ABC):
    """Abstract base class for all data providers"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier"""
        pass

    @abstractmethod
    async def get_ohlcv(
        self, symbol: str, timeframe: str = "1h", limit: int = 100, since: int | None = None
    ) -> list[Candle]:
        """
        Fetch OHLCV candlestick data

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d, 1w)
            limit: Number of candles to fetch
            since: Epoch ms to start from; None fetches the most recent candles

        Returns:
            List of Candle objects, oldest first
        """
        pass

    @abstractmethod
    async def get_symbols(self) -> list[SymbolInfo]:
        """
        Get list of available trading pairs

        Returns:
            List of SymbolInfo objects
        """
        pass

    @abstractmethod
    async def get_ticker_price(self, symbol: str) -> float | None:
        """
        Get current price for a symbol

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")

        Returns:
            Current price or None if not available
        """
        pass

    @abstractmethod
    async def get_all_tickers(self) -> dict:
        """
        Fetch all tickers at once.

        Returns:
            Dict of {symbol: ticker_dict}
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the underlying exchange connection and release resources."""
        pass
