# Oracle Intelligence Analytics Suite

The Oracle Intelligence suite provides professional-grade market screening and quantitative analysis for the top cryptocurrencies.

## Overview

The analytics engine focuses on five key dimensions of market data:

1. **Trend & Momentum** (Oracle Screener)
2. **Aggregate Sentiment** (Market Health)
3. **Institutional Liquidity** (Liquidity Map)
4. **Volatility Exhaustion** (Contrarian Radar)
5. **Relative Alpha** (Relative Strength)

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

## API Usage

Refer to [API.md](./API.md) for endpoint details. Most endpoints now accept:

- `limit`: Number of coins to analyze (e.g. `?limit=50`).
- `timeframe`: Horizon to analyze (e.g. `?timeframe=4h`).
