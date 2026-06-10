"""Application-wide constants."""

# Maps CCXT-style timeframe strings to their duration in milliseconds.
TIMEFRAME_MS: dict[str, int] = {
    "1m": 60 * 1_000,
    "5m": 5 * 60 * 1_000,
    "15m": 15 * 60 * 1_000,
    "30m": 30 * 60 * 1_000,
    "1h": 60 * 60 * 1_000,
    "2h": 2 * 60 * 60 * 1_000,
    "4h": 4 * 60 * 60 * 1_000,
    "6h": 6 * 60 * 60 * 1_000,
    "8h": 8 * 60 * 60 * 1_000,
    "12h": 12 * 60 * 60 * 1_000,
    "1d": 24 * 60 * 60 * 1_000,
    "3d": 3 * 24 * 60 * 60 * 1_000,
    "1w": 7 * 24 * 60 * 60 * 1_000,
}

# Default fallback if timeframe not found (1 hour)
DEFAULT_TIMEFRAME_MS: int = 60 * 60 * 1_000

# 0.1% simulated round-trip fee (paper trading)
FEE_PCT = 0.001
