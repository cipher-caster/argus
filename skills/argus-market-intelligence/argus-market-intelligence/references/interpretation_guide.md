# Argus Interpretation Reference

Use this guide to translate raw API data into structured intelligence.

## Oracle Earnest Score
| Score | Meaning | Action |
|-------|---------|--------|
| +3 to +4 | STRONG BUY | High conviction long |
| +1 to +2 | BUY | Moderate bullish |
| 0 | NEUTRAL | No edge |
| -1 to -2 | SELL | Moderate bearish |
| -3 to -4 | STRONG SELL | High conviction short |

## Oracle States
- **TRENDING**: Strong directional move; ride the trend.
- **RANGING**: Consolidation; use tighter take-profit (TP), avoid chasing entries.
- **VOLATILE**: High Average True Range (ATR); reduce position size, use wider stop-losses.

## Titan Signals
- **BUY / SELL**: Market entry now; trend confirmed.
- **BUY_LIMIT / SELL_LIMIT**: Wait for pullback to specified limit entry price.
- **WAIT_OB**: Wait for Oversold Bounce (mean reversion setup).
- **WAIT_OS**: Wait for Overbought Rejection.

## MTF Confluence (Eliz + Mayne Framework)
*Data from `analytics/best-setups` or MTF stack.*
- **Eliz lane**: 4H (entry trigger) + 1D (swing structure).
- **Mayne lane**: 12H (higher-TF bias) + 1W (macro direction).
- **4 Confirmed**: Maximum conviction.
- **2–3 Confirmed**: Tradeable but size down.
- **0–1 Confirmed**: Avoid; no confluence.

## Win Rate Context
- **Break-even at 2:1 RR**: 33.3%.
- **< 33%**: Historically unprofitable; trade with caution.
- **33–50%**: Acceptable.
- **> 50%**: Edge confirmed; can size up.
