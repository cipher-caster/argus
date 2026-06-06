# Error Handling in Argus Backend

This document describes the error handling patterns and custom exception usage in the Argus backend.

## Custom Exception Hierarchy

Argus uses a hierarchy of domain-specific exceptions for better error handling and debugging:

```
Exception (Python base)
└── ArgusException (Argus base)
    ├── DataProviderError
    ├── CacheError
    ├── CalculationError
    └── ValidationError
```

## Exception Types

### ArgusException

**Base class** for all Argus-specific errors.

- Use when catching any Argus error generically
- All other custom exceptions inherit from this

### DataProviderError

**Raised when external data provider fails**

Common scenarios:

- Binance API timeout
- CoinGecko rate limit exceeded
- Invalid response from exchange
- Network errors connecting to external APIs

```python
from app.exceptions import DataProviderError

try:
    data = await provider.get_ticker(symbol)
except APITimeout:
    raise DataProviderError(f"Binance API timeout for {symbol}")
```

### CacheError

**Raised when Redis cache operation fails**

Common scenarios:

- Redis connection refused
- Cache key not found when expected
- JSON serialization/deserialization errors

```python
from app.exceptions import CacheError

try:
    data = await RedisClient.get_json("market:tickers")
    if data is None:
        raise CacheError("market:tickers cache key not found")
except RedisConnectionError as e:
    raise CacheError(f"Redis connection failed: {e}")
```

### CalculationError

**Raised when indicator calculation fails**

Common scenarios:

- Insufficient data for indicator (e.g., need 14 rows for RSI)
- Invalid indicator parameters
- Mathematical errors (division by zero, etc.)

```python
from app.exceptions import CalculationError

if len(df) < period:
    raise CalculationError(
        f"Insufficient data for RSI: need {period} rows, got {len(df)}"
    )
```

### ValidationError

**Raised when input validation fails**

Common scenarios:

- Invalid symbol format
- Invalid timeframe parameter
- Out of range parameters

```python
from app.exceptions import ValidationError

allowed_timeframes = ['1h', '4h', '1d']
if timeframe not in allowed_timeframes:
    raise ValidationError(
        f"Invalid timeframe '{timeframe}', must be one of {allowed_timeframes}"
    )
```

## Logging Best Practices

### Structured Logging with Context

Always include context in log messages:

```python
import logging
logger = logging.getLogger(__name__)

# Good: Structured with context
logger.info(f"Fetched {len(candles)} candles for {symbol} {timeframe}")
logger.error(f"Provider error fetching {symbol}: {e}")

# Bad: Generic messages
logger.info("Fetched data")
logger.error(f"Error: {e}")
```

### Log Levels

- **DEBUG**: Detailed diagnostic information (cache hits, skipped symbols)
- **INFO**: General informational messages (successful operations, counts)
- **WARNING**: Unexpected but handled situations (missing data, fallbacks)
- **ERROR**: Error conditions that need attention (failures, exceptions)

```python
logger.debug(f"Cache hit for ticker:{symbol}")
logger.info(f"Fetched {len(symbols)} symbols from provider")
logger.warning(f"Ticker not found for {symbol}")
logger.error(f"Unexpected error fetching {symbol}: {e}", exc_info=True)
```

### Exception Logging Pattern

```python
try:
    result = await risky_operation()
except DataProviderError as e:
    logger.error(f"Provider error in operation: {e}")
    raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")
except ValidationError as e:
    logger.warning(f"Validation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)  # Include traceback
    raise HTTPException(status_code=500, detail="Internal server error")
```

## HTTP Status Code Mapping

Map custom exceptions to appropriate HTTP status codes:

| Exception           | HTTP Status               | Meaning                    |
| ------------------- | ------------------------- | -------------------------- |
| `ValidationError`   | 400 Bad Request           | Invalid input parameters   |
| `DataProviderError` | 503 Service Unavailable   | External service down      |
| `CacheError`        | 503 Service Unavailable   | Redis unavailable          |
| `CalculationError`  | 500 Internal Server Error | Internal processing failed |
| Generic `Exception` | 500 Internal Server Error | Unexpected error           |

## Error Message Guidelines

1. **Be Specific**: Include what failed and why
   - ❌ "Failed to fetch data"
   - ✅ "Failed to fetch BTC/USDT 1h candles: API timeout after 30s"

2. **Include Context**: Add symbol, timeframe, parameters
   - ❌ "Invalid parameter"
   - ✅ "Invalid timeframe '2h': must be one of ['1h', '4h', '1d']"

3. **Actionable**: Help debugging
   - ❌ "Error occurred"
   - ✅ "Insufficient data for RSI: need 14 rows, got 5"

4. **User-Friendly for APIs**: Don't expose internal details
   - ❌ Expose database connection strings
   - ✅ "Cache unavailable, please try again"

## Testing Error Handlers

Test both success and failure paths:

```python
@pytest.mark.asyncio
async def test_fetch_ohlcv_provider_failure(mock_provider):
    """Should raise DataProviderError on provider timeout"""
    mock_provider.get_candles.side_effect = DataProviderError("API timeout")

    with pytest.raises(HTTPException) as exc_info:
        await get_ohlcv("BTC/USDT", "1h", 100)

    assert exc_info.value.status_code == 503
    assert "Service unavailable" in exc_info.value.detail
```

## Migration Checklist

When refactoring existing error handling:

- [ ] Import custom exceptions at top of file
- [ ] Add logging import and create logger
- [ ] Replace broad `except Exception` with specific exception types
- [ ] Add context to log messages (symbol, timeframe, etc.)
- [ ] Use `exc_info=True` for unexpected errors
- [ ] Map exceptions to appropriate HTTP status codes
- [ ] Write tests for error scenarios
- [ ] Update docstrings to document raised exceptions
