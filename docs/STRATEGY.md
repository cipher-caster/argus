# Argus Oracle Strategy (v9.0)

The **Argus Oracle** is a unified predictive analytics engine that ports logic from the **Earnest v2.6** and **Prophet v9.0** TradingView scripts into the Argus platform.

## Architecture

The strategy uses a **confluence-based voting system** across multiple timeframes to determine market bias and entry signals.

### 1. The Earnest "Brain" (Micro-Analysis)
Calculated on the active chart timeframe (e.g., 1H, 15m). It uses 4 voters to generate a confidence score:

| Voter | Logic | Bullish | Bearish |
|-------|-------|---------|---------|
| **RSI** | Momentum | 50 < RSI < 70 | 30 < RSI < 50 |
| **Bollinger** | Volatility | Price > Upper + 10% | Price < Lower - 10% |
| **ADX** | Strength | Trend > 20 & P > EMA | Trend > 20 & P < EMA |
| **EMA** | Trend | Price > EMA 200 | Price < EMA 200 |

### 2. The Prophet "Macro" (Big Picture)
Calculated on the Daily (1D) timeframe to ensure the micro-signal aligns with the broader trend:

- **Titan Trend**: Price vs EMA 200 (Daily).
- **Ichimoku Cloud**: Price vs Leading Spans.
- **Volume Flow**: On-Balance Volume (OBV) vs its 20-period moving average.

## Signals

- **STRONG BUY**: Macro Bullish + Earnest Score >= 3.
- **BUY**: Earnest Score >= 3 (Macro Neutral or early reversal).
- **STRONG SELL**: Macro Bearish + Earnest Score <= -3.
- **SELL**: Earnest Score <= -3.

## Visual Integration

### Oracle Panel
A high-contrast, floating panel on the chart providing:
- Real-time Signal & Confidence.
- Macro Bias breakdown.
- Human-readable advice.
- Target & Stop Loss levels (calculated via ATR).

### Chart Markers
Historical BUY/SELL arrows are plotted directly on the main series, allowing for visual backtesting and verification of strategy efficacy.

## Implementation Details

- **Backend**: `app/strategies/oracle.py` (Pandas + Pandas-TA).
- **Frontend**: `useStrategyOracle` hook + `StrategyOraclePanel` component.
- **Data**: Orchestrated to fetch both micro and macro candle history in a single request.
