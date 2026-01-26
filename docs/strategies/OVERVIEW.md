# Argus Trading Strategies

Argus includes professional-grade trading strategies ported from Pine Script (TradingView) to Python, allowing for real-time market scanning and live backtesting.

## Available Strategies

You can toggle these strategies from the **Indicators** menu on any chart.

### 1. Prophet Strategy (v9.0) - Trend Following

The core engine of Argus. A robust swing-trading strategy that combines "Earnest" momentum scoring with a "Macro Context" filter.

- **Logic**: Earnest Brain (RSI, Bollinger, ADX, EMA) + Daily Trend Filter.
- **Signals**: Fires when momentum aligns with the **Titan Trend** (Daily).
- **Best for**: Trend following on 1H/4H timeframes.

---

## The "Earnest Brain" (Voting System)

The strategy uses a confluence-based voting system to generate a confidence score:

| Voter         | Logic      | Bullish (+1)           | Bearish (-1)           |
| ------------- | ---------- | ---------------------- | ---------------------- |
| **RSI**       | Momentum   | 50 < RSI < 70          | 30 < RSI < 50          |
| **Bollinger** | Volatility | Breaking out above Mid | Breaking out below Mid |
| **ADX**       | Strength   | Trend > 20 & P > EMA   | Trend > 20 & P < EMA   |
| **EMA**       | Trend      | Price > EMA 200        | Price < EMA 200        |

---

## Live Backtesting & Performance

Argus runs a real-time simulation on all visible chart history to calculate the efficacy of the selected strategy.

### Performance Metrics

Displayed in the floating **Strategy Panel**:

- **Win Rate**: Percentage of trades that hit Target (3R) before Stop Loss (1.5R).
- **Net PnL**: Cumulative percentage gain/loss across all simulated trades.
- **Total Trades**: Number of signals detected in the current history.

### Visual Verification

- **Arrows**: Green (Buy) and Red (Sell) markers are plotted on historical candles where the strategy entered.
- **Advice**: A human-readable summary of the current market state and trade potential.

---

## Implementation Details

- **Backend Engine**: `backend/app/strategies/oracle.py`
- **Backtest Logic**: `_run_backtest()` simulates trades with ATR-based targets.
- **API Endpoint**: `GET /api/strategy/oracle/{symbol}`
