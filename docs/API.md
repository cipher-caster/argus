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

### Get Market Coins

`GET /market/coins`

Returns the paginated and sorted merged market data list (Snapshot + Live Overlay).

**Query Parameters:**

- `page`: Page number (default 1)
- `page_size`: Items per page (default 50)
- `search`: Filter by symbol string
- `sort_by`: `market_cap` (default), `price`, `volume_24h`, `change_1h`, `change_24h`, `change_7d`
- `sort_order`: `desc` (default) or `asc`

**Response Fields (CoinInfo):**

- `rank`: Market cap rank
- `symbol`: e.g. "BTC/USDT"
- `name`: Full name
- `price`: Current price
- `change_1h`: 1h % change
- `change_24h`: 24h % change
- `change_7d`: 7d % change
- `market_cap`: Market capitalization
- `volume_24h`: 24h Volume
- `sparkline_in_7d`: [Array of 168 floats]
- `image`: URL to logo
- `high_24h`: 24h high price
- `low_24h`: 24h low price

### Get Market Summary

`GET /market/summary`

Returns top performers and aggregate stats.

**Response Fields:**

- `total_coins`: Count of coins in registry
- `top_gainers`: List of top 5 gainers (CoinInfo)
- `top_losers`: List of top 5 losers (CoinInfo)
- `top_volume`: List of top 5 volume leaders (CoinInfo)

`GET /ticker/{symbol}`
Returns the current price and metadata for a single symbol.

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

## Tech Indicators

### Dashboard Indicators

`GET /indicators/market/dashboard`

Returns market-level indicators for the dashboard cards.

**Response:**

- `btc_volatility`: BTC price volatility (1-100 scale, 14-day)
- `market_adx`: ADX trend strength (0-100, on BTC/USDT daily)
- `total_market_cap`: Total 24h volume of top 100 coins + regime
- `btc_dominance`: BTC volume share among top 100 coins

### Calculate Indicator

`POST /indicators/calculate`

Calculates technical indicators on OHLCV data.

**Body:**

```json
{
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "limit": 300,
  "indicators": [
    { "type": "ema", "params": { "length": 20 } },
    { "type": "rsi", "params": { "length": 14 } }
  ]
}
```

**Available Indicators**: `ema`, `sma`, `rsi`, `macd`, `bbands`, `obv`, `linreg`
