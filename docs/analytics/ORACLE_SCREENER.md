# Oracle Screener (The Prophet)

**The Oracle Screener** is the primary signal engine of the platform. It uses the **Prophet** trading strategy (v9.0) to generate tactical Buy/Sell signals.

## The Earnest Score

Every asset is given a score from **-4 to +4** based on a voting system (the "Earnest Brain"). Positive = bullish momentum, negative = bearish.

### The Voters

The score is the sum of four independent voters. Implementation: `backend/app/strategies/oracle.py → _calculate_earnest_score()`

| Voter | Bullish (+1) | Bearish (-1) | Neutral (0) |
|---|---|---|---|
| **RSI** | 50 < RSI < 70 | 30 < RSI < 50 | RSI ≥ 70 or ≤ 30 (extremes excluded) |
| **Bollinger** | BB position > 0.1 (above mid) | BB position < -0.1 (below mid) | Near midband |
| **ADX** | ADX > 20 AND price > EMA200 | ADX > 20 AND price < EMA200 | ADX ≤ 20 (chop) |
| **EMA** | Price > EMA200 | Price < EMA200 | — |

> BB position = `(close - bb_mid) / (bb_upper - bb_lower)`

### The Scorecard

- **+4 / +3**: **STRONG BUY** — high-probability trend following
- **+1 / +2**: **WEAK BUY** — wait for confirmation
- **0**: **NEUTRAL** — do not trade
- **-1 / -2**: **WEAK SELL**
- **-3 / -4**: **STRONG SELL**

## Macro Bias (Prophet Filter)

The Oracle also runs a macro check on the daily timeframe via `_calculate_macro_bias()`:

| Check | Condition |
|---|---|
| Trend | Price > EMA200 |
| Cloud | Price > Ichimoku Cloud Top |
| OBV | OBV > OBV 20-period SMA |

- Score ≥ 2 → **BULLISH**
- Score = 1 → **NEUTRAL**
- Score = 0 → **BEARISH**

Signal synthesis (`_synthesize_signal()`):
- Macro ≥ 2 AND Earnest ≥ 3 → `STRONG_BUY`
- Earnest ≥ 3 (any macro) → `BUY`
- Macro = 0 AND Earnest ≤ -3 → `STRONG_SELL`
- Earnest ≤ -3 (any macro) → `SELL`

## Market State

The Oracle classifies the asset's volatility regime via `_detect_market_state()`:

- **SLEEPING**: ADX ≤ 20. Choppy/ranging. Do not trade breakouts.
- **TRENDING**: 20 < ADX ≤ 40. Normal trending conditions.
- **SUPER TREND**: ADX > 40. Strong directional move.

Volatility tag (based on normalized ATR = `atr/close * 100`):
- **STABLE**: norm_atr < 0.5%
- **ACTIVE**: 0.5–2%
- **DANGER**: > 2% — reduce leverage
