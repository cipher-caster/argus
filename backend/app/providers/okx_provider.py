"""
OKX Data Provider
Uses CCXT library for market data fetching
"""

import ccxt.async_support as ccxt

from .data_provider import Candle, DataProvider, SymbolInfo


class OKXProvider(DataProvider):
    """OKX exchange data provider via CCXT"""

    def __init__(self):
        self._exchange = ccxt.okx(
            {
                "enableRateLimit": True,
                "timeout": 15000,  # 15s — avoids hanging on slow OKX endpoints
                "options": {
                    "defaultType": "spot",
                    # Only load spot markets — skips FUTURES/SWAP/OPTIONS fetches
                    # which are slow and not needed for USDT pair screener
                    "fetchMarkets": ["spot"],
                },
            }
        )
        self._symbols_cache: list[SymbolInfo] | None = None

    @property
    def name(self) -> str:
        return "okx"

    async def _ensure_loaded(self):
        """Load markets if not already loaded"""
        if not self._exchange.markets:
            await self._exchange.load_markets()

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Convert Binance-style symbol (BTCUSDT) to CCXT slash format (BTC/USDT)."""
        if "/" not in symbol and symbol.endswith("USDT"):
            return symbol[:-4] + "/USDT"
        return symbol

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        since: int = None,  # Timestamp in ms to fetch data starting from
    ) -> list[Candle]:
        await self._ensure_loaded()

        # Request limit+1 so we can drop the still-forming candle at the tail
        ohlcv = await self._exchange.fetch_ohlcv(
            self._normalize_symbol(symbol), timeframe=timeframe, limit=limit + 1, since=since
        )

        # Drop the last row — it is the currently-forming (incomplete) candle
        ohlcv = ohlcv[:-1] if ohlcv else ohlcv

        candles = []
        for item in ohlcv:
            candles.append(
                Candle(
                    timestamp=item[0],
                    open=item[1],
                    high=item[2],
                    low=item[3],
                    close=item[4],
                    volume=item[5],
                )
            )

        return candles

    async def get_symbols(self) -> list[SymbolInfo]:
        await self._ensure_loaded()

        if self._symbols_cache:
            return self._symbols_cache

        symbols = []
        for symbol, market in self._exchange.markets.items():
            if market.get("quote") == "USDT" and market.get("active"):
                symbols.append(
                    SymbolInfo(
                        symbol=symbol, base=market.get("base", ""), quote=market.get("quote", "")
                    )
                )

        self._symbols_cache = symbols
        return symbols

    async def get_ticker_price(self, symbol: str) -> float | None:
        await self._ensure_loaded()

        try:
            ticker = await self._exchange.fetch_ticker(self._normalize_symbol(symbol))
            return ticker.get("last")
        except Exception:
            return None

    async def get_all_tickers(self) -> dict:
        """Fetch all tickers at once - much faster than individual calls"""
        await self._ensure_loaded()

        try:
            return await self._exchange.fetch_tickers()
        except Exception:
            return {}

    async def close(self):
        """Close the exchange connection"""
        await self._exchange.close()
