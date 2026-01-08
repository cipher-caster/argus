# API Documentation

The Argus Backend provides a RESTful API built with FastAPI.

**Base URL**: `http://localhost:8000/api`

---

## Market Data

### Get OHLCV Candles

`GET /ohlcv/{symbol}`

Fetches historical candlestick data.

- **Parameters**:
  - `symbol` (path): e.g., `BTC/USDT`
  - `timeframe` (query): `1m`, `5m`, `15m`, `1h` (default), `4h`, `1d`
  - `limit` (query): Number of candles (max 1000)
  - `end_timestamp` (query, optional): Fetch candles before this timestamp (ms)

### Get Ticker

`GET /ticker/{symbol}`
Returns the current price.

---

## Analytics

### Funding Rate

`GET /analytics/funding-rate/{symbol}`
Returns historical funding rate history.

- **Limit**: Default 500 records

### Open Interest

`GET /analytics/open-interest/{symbol}`
Returns open interest history.

- **Period**: `5m`, `15m`, `1h`, `4h`, `1d`

### Long/Short Ratio

`GET /analytics/long-short-ratio/{symbol}`
Returns global account long/short ratio.

---

## Liquidation Heatmap

### Get Heatmap Buckets

`GET /liquidation/heatmap`

Returns aggregated liquidation volume buckets for visualization.

- **Parameters**:
  - `symbol`: e.g. `BTCUSDT`
  - `timeframe`: `1h`, `4h`, `12h`, `24h`
- **Response**:
  ```json
  [
    {
      "timestamp": 1704123456789,
      "price_buckets": {
        "42000": 150000.5,
        "42050": 20000.0
      }
    }
  ]
  ```

---

## Tech Indicators

### Calculate Indicator

`GET /indicators/{name}/{symbol}`

Calculates technical indicators on demand.

- **Name**: `rsi`, `macd`, `bollinger`, `ema`, `sma`
- **Parameters**: Indicator-specific (e.g., `period=14`)
