# API Documentation

The Argus Backend provides a RESTful API built with FastAPI.

**Base URL**: `http://localhost:8000/api`

---

## Market Data

### Get OHLCV Candles

`GET /ohlcv/{symbol}`

Fetches historical candlestick data.

- **Parameters**:
  - `symbol` (path): e.g., `BTCUSDT`
  - `timeframe` (query): `1m`, `5m`, `15m`, `1h` (default), `4h`, `12h`, `1d`, `1w`
  - `limit` (query): Number of candles (max 1000)
  - `end_timestamp` (query, optional): Fetch candles before this timestamp (ms)

### Get Market Coins

`GET /market/coins`

Returns the paginated and sorted merged market data list.

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
- `change_1h`, `change_24h`, `change_7d`: % changes
- `market_cap`, `volume_24h`: Cap and volume
- `sparkline_in_7d`: Array of 168 floats
- `image`: Logo URL
- `high_24h`, `low_24h`: 24h range

### Get Market Summary

`GET /market/summary`

Returns top performers and aggregate stats.

**Response Fields:**

- `total_coins`: Count of coins in registry
- `top_gainers`, `top_losers`, `top_volume`: Top 5 each (CoinInfo)

### Get Ticker

`GET /ticker/{symbol}`

Returns the current price for a single symbol.

---

## Analytics

### Oracle Screener

`GET /analytics/screener`

Oracle Prophet v9.0 analysis (Earnest score -4 to +4, bias, state) for top coins.

**Query Parameters:**

- `limit`: Number of coins (default 50)
- `timeframe`: `1h` (default), `4h`, `1d`

### Relative Strength

`GET /analytics/relative-strength`

Compares altcoin performance vs BTC benchmark.

**Query Parameters:**

- `limit`: Number of coins (default 50)
- `timeframe`: `1h` (default), `4h`, `1d`

### Contrarian Radar

`GET /analytics/contrarian-radar`

Identifies coins overextended from their mean (ATR-based).

**Query Parameters:**

- `limit`: Number of coins (default 50)
- `timeframe`: `1h` (default), `4h`, `1d`

### Signal Summary

`GET /analytics/signal-summary`

High-level market overview for the dashboard. Analyzes top 20 symbols.

**Response Fields:**

- `bullish_pct`, `bearish_pct`: % of coins with strong Oracle scores
- `top_signals`: List of up to 5 signal strings
- `market_state`: `STRONG BULL`, `STRONG BEAR`, `NEUTRAL`, or `SLEEPING`

### Best Setups

`GET /analytics/best-setups`

High-conviction setups where Oracle and Titan agree on direction. Max 10 results sorted by conviction (0–100).

**Query Parameters:**

- `timeframe`: Titan timeframe (default `4h`)
- `limit`: Coin pool size (default 50)

**Response Fields (BestSetupItem):**

- `symbol`, `direction`: `LONG` or `SHORT`
- `conviction`: 0–100 composite score (Oracle 40pts + Titan 40pts + bonuses)
- `entry`, `tp`, `sl`: Price targets
- `reason`: Human-readable Oracle + Titan summary
- `oracle_score`: Earnest score (-4 to +4)
- `titan_signal`: Titan signal string
- `win_rate`: Oracle backtest win rate %. `null` when `total_trades < 10`
- `total_trades`: Backtest trade count. `null` when < 10
- `timeframe_confirmation`: Eliz+Mayne MTF confluence — `{"4h": bool, "1d": bool, "12h": bool, "1w": bool}`. Titan confirmed on each TF

### Titan Radar

`GET /analytics/titan-radar`

Titan Unified System scanner across the top coins.

**Query Parameters:**

- `limit`: Number of coins (default 50)
- `timeframe`: (default `4h`)

**Response Fields (TitanRadarItem):**

- `symbol`, `price`, `signal`, `confidence`, `trend`, `momentum`, `volatility`
- `entry`, `tp`, `sl`: Price targets
- `advice`: Sizing/risk text
- `reasons`: List of signal reason strings

---

## Strategy

### Oracle Strategy

`GET /strategy/oracle/{symbol}`

Full Oracle Prophet v9.0 analysis for a single coin.

**Query Parameters:**

- `micro_tf`: Trading timeframe (default `1h`)
- `macro_tf`: Trend timeframe (default `1d`)

**Response includes:** signal, bias, state, earnest voters, targets, historical signals, backtest performance.

### Titan Strategy

`GET /strategy/titan/{symbol}`

Full Titan Unified System analysis for a single coin.

**Query Parameters:**

- `timeframe` (default `4h`)

---

## Tech Indicators

### Dashboard Indicators

`GET /indicators/market/dashboard`

Market-level indicators for the dashboard cards.

**Response:**

- `btc_volatility`: BTC price volatility (1–100, 14-day)
- `market_adx`: ADX trend strength (0–100, on BTC daily)
- `total_market_cap`: Top 100 coins 24h volume + regime
- `btc_dominance`: BTC volume share among top 100 coins

### Calculate Indicator

`POST /indicators/calculate`

Calculates technical indicators on OHLCV data.

**Body:**

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "limit": 300,
  "indicators": [
    { "type": "ema", "params": { "length": 20 } },
    { "type": "rsi", "params": { "length": 14 } }
  ]
}
```

**Available Indicators**: `ema`, `sma`, `rsi`, `macd`, `bbands`, `obv`, `linreg`
