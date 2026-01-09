# Argus Trading Strategies

Argus includes professional-grade trading strategies ported from Pine Script (TradingView) to Python, allowing for real-time market scanning and live backtesting.

## Available Strategies

You can toggle these strategies from the **Indicators** menu on any chart.

### 1. Earnest Strategy (v2.6) - Pure Momentum
A high-frequency scalping strategy that focuses on immediate price action and momentum. It ignores the daily trend to capture fast moves.

*   **Logic**: Uses the 4-voter "Brain" (RSI, Bollinger, ADX, EMA).
*   **Signals**: Fires whenever momentum confluence is high (Score >= 3).
*   **Best for**: Lower timeframes (1m, 5m, 15m) and range-bound markets.

### 2. Prophet Strategy (v9.0) - Trend Following
A robust swing-trading strategy that adds a "Macro Context" filter to the Earnest engine. It only takes trades that align with the daily trend.

*   **Logic**: Earnest Brain + Daily Trend Filter (EMA 200, Ichimoku Cloud, OBV Volume).
*   **Signals**: Fires when momentum aligns with the **Titan Trend** (Daily).
*   **Best for**: Higher timeframes (1H, 4H) and trending markets.

---

## The "Earnest Brain" (Voting System)

Both strategies use a confluence-based voting system to generate a confidence score:

| Voter | Logic | Bullish (+1) | Bearish (-1) |
|-------|-------|---------|---------|
| **RSI** | Momentum | 50 < RSI < 70 | 30 < RSI < 50 |
| **Bollinger** | Volatility | Breaking out above Mid | Breaking out below Mid |
| **ADX** | Strength | Trend > 20 & P > EMA | Trend > 20 & P < EMA |
| **EMA** | Trend | Price > EMA 200 | Price < EMA 200 |

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
- **API Endpoint**: `GET /api/strategy/oracle/{symbol}?strategy_mode=[prophet\|earnest]`