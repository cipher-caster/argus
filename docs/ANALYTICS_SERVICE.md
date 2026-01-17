# Oracle Intelligence Analytics Suite

The Oracle Intelligence suite provides professional-grade market screening and quantitative analysis for the top cryptocurrencies.

## Overview

The analytics engine focuses on five key dimensions of market data:

1. **Trend & Momentum** (Oracle Screener)
2. **Aggregate Sentiment** (Market Health)
3. **Institutional Liquidity** (Liquidity Map)
4. **Volatility Exhaustion** (Contrarian Radar)
5. **Relative Alpha** (Relative Strength)

6. **Relative Alpha** (Relative Strength)

## Detailed Documentation

For a deep dive into the logic, thresholds, and trading actionable for each engine, read the dedicated guides:

- **[The Trend God (Trend Radar)](./analytics/TREND_RADAR.md)**
- **[The Weekly Trap (Structure)](./analytics/WEEKLY_TRAP.md)**
- **[The Confluence Engine](./analytics/CONFLUENCE_ENGINE.md)**
- **[Oracle Screener](./analytics/ORACLE_SCREENER.md)**
- **[Market Health](./analytics/MARKET_HEALTH.md)**
- **[Contrarian Radar](./analytics/CONTRARIAN_RADAR.md)**

## Core Components

### 1. Dynamic Market Data Service

Located at `backend/app/services/market_data.py`, this service centralizes the retrieval of high-impact assets.

- **Scope**: Targets the Top 250 coins by market cap and volume.
- **Filtering**: Automatically filters for active Binance Futures pairs to ensure all analytics results are actionable for traders.
- **Aggregation**: Merges CoinGecko metadata (rank, category) with live Binance price action.

### 2. Multi-Timeframe Engine

All analytics modules support dynamic timeframe switching:

- **1h (Default)**: Intraday momentum and immediate volatility shifts.
- **4h**: Swing-trading trends and structural reclaims.
- **1d**: Macro trend alignment and extreme mean-reversion exhaustion.

## Analytics Modules

### Oracle Screener

- **Logic**: Combines EMA trend alignment, ADX strength, and RSI momentum.
- **Scoring**: Returns an "Earnest Score" from -4 (Strongly Bearish) to +4 (Strongly Bullish).
- **Target**: Top 50 highest-volume symbols.

### Market Health

- **Logic**: Aggregates the percentage of the market trading above/below the 200-period EMA.
- **Volatility Squeeze**: Detects Bollinger Band & Keltner Channel compression across the Top 100 symbols.
- **Use Case**: Determining overall market "regime" (Strong Bull, Neutral, or Danger).

### Liquidity Map

- **Logic**: Identifies SFPs (Swing Failure Patterns) and reclaims of Previous Weekly Highs/Lows.
- **Entry Signals**: Bull/Bear sweeps indicating institutional liquidity engineering before reversals.

### Contrarian Radar

- **Logic**: Monitors extreme ATR (Average True Range) extensions from the mean.
- **Setup**: Identifies "Overstretched" pairs likely to return to their EMA.

### Relative Strength

- **Logic**: Measures performance vs. Bitcoin (BTCUSDT cluster).
- **Alpha Hunting**: Find altcoins that are gaining value even when BTC is stagnant or dropping.

## Frontend Components

(Dashboard Architecture)

The analytics data is visualized through a responsive dashboard system located in `frontend/src/components/features/dashboard`.

### Indicator Cards

Standardized widget system displaying key market metrics:

- **Visuals**: Configurable Gauge bar and/or SVG Sparkline for 7-day trend.
- **Metrics**:
  - **MADX**: Trend Strength (0-100)
  - **Avg Crypto RSI**: Momentum (0-100)
  - **Total Market Cap**: Aggregate Value
  - **BTC Dominance**: Market Share %

### Oracle Intelligence Card

A special indicator card integrating the Oracle Signal Summary:

- **Confidence**: AI-driven bullish/bearish confidence score.
- **Alpha Signals**: Live list of the top 3 high-conviction signals.
- **Design**: Matches the visual rhythm of standard indicator cards.

### Responsive Grid

The dashboard uses an adaptive grid layout:

- **Desktop**: 5 columns (All cards in one row).
- **Tablet**: 2 columns (Balanced 2x3 grid).
- **Mobile**: 1 column (Vertical stack).

## API Usage

Refer to [API.md](./API.md) for endpoint details. Most endpoints now accept:

- `limit`: Number of coins to analyze (e.g. `?limit=50`).
- `timeframe`: Horizon to analyze (e.g. `?timeframe=4h`).

## Performance & Caching

The analytics suite uses **Redis caching** for fast responses:

### Cache-Aside Pattern

All endpoints check Redis first, compute on miss, then cache results:

| Endpoint             | Cache Key                           | TTL |
| -------------------- | ----------------------------------- | --- |
| `/screener`          | `analytics:screener:{tf}:{limit}`   | 60s |
| `/market-health`     | `analytics:health:{tf}:{limit}`     | 60s |
| `/liquidity-sweeps`  | `analytics:liquidity:{tf}:{limit}`  | 60s |
| `/relative-strength` | `analytics:strength:{tf}:{limit}`   | 60s |
| `/contrarian-radar`  | `analytics:contrarian:{tf}:{limit}` | 60s |
| `/signal-summary`    | `analytics:signal-summary`          | 60s |

### Worker Pre-warming

The `sync_analytics_cache` job runs every 5 minutes to pre-compute analytics for 1h, 4h, and 1d timeframes. This ensures near-instant responses for common requests.

### Monitoring

```bash
# Check cached keys
docker compose exec redis redis-cli KEYS "analytics:*"

# Check TTL of a key
docker compose exec redis redis-cli TTL "analytics:screener:1h:50"
```
