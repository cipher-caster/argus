# Oracle Screener (The Prophet)

**The Oracle Screener** is the primary signal engine of the platform. It uses the **Prophet** trading strategy (v9.0) to generate tactical Buy/Sell signals.

## The Earnest Score

Every asset is given a "Confidence Score" from **0 to 4** based on a voting system. Call this the "Earnest Score".

### The Voters

The score is the sum of four independent voters. If they agree, the score is high. If they disagree, the score is low.

1.  **RSI Voter**:
    - **Bull Vote (+1)**: RSI between 50-70 (Trend Strength) or Bullish Divergence.
    - **Bear Vote (-1)**: RSI < 50 or Bearish Divergence.
2.  **Bollinger Voter**:
    - **Bull Vote (+1)**: Price above Middle Band + Bandwidth expanding.
    - **Bear Vote (-1)**: Price below Middle Band.
3.  **EMA Trend Voter**:
    - **Bull Vote (+1)**: Price > 20 EMA > 50 EMA.
    - **Bear Vote (-1)**: Price < 20 EMA < 50 EMA.
4.  **ADX Momentum Voter**:
    - **Bull Vote (+1)**: ADX > 25 (Strong Trend).
    - **Neutral (0)**: ADX < 25 (Chop).

### The Scorecard

- **+4 / +3**: **STRONG BUY** (High probability trend following).
- **+1 / +2**: **WEAK BUY** (Wait for confirmation).
- **0**: **NEUTRAL** (Do not trade).
- **-1 / -2**: **WEAK SELL**.
- **-3 / -4**: **STRONG SELL**.

## Market State & Liquidity

The Oracle also classifies the specific asset's state:

- **SLEEPING**: Low volatility. Do not trade breakouts.
- **ACTIVE**: Normal volatility. Good for trading.
- **DANGER**: High volatility. Stop-hunts likely. Manage risk tightly.

## Relative Strength (vs BTC)

The Screener compares the asset's performance to Bitcoin over the same timeframe.

- **STRONG**: Outperforming BTC (Alpha). Focus on Longs here during Bull runs.
- **WEAK**: Underperforming BTC. Avoid Longs even if the signal is buy (Beta lag).
