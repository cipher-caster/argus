# Argus Report Templates

Use these templates to structure Argus API data.

## Market Report
Includes pulse, top signals, screener, and best setups.

```markdown
## Argus Market Report — {current time}

### Market Pulse
- State: {signal_summary.market_state}
- Sentiment: {signal_summary.bullish_pct}% Bullish / {signal_summary.bearish_pct}% Bearish
- BTC Dominance: {dashboard.btc_dominance}%
- BTC Volatility: {dashboard.btc_volatility}/100
- ADX Trend Strength: {dashboard.market_adx}/100

### Top Signals Right Now
{signal_summary.top_signals — list each one}

### Oracle Screener Highlights (1H)
List top 5 by absolute score:
- {symbol} | Score {score} | {bias} | {state} | {opportunity}

### Best Setups (4H — Oracle + Titan Confluence)
List top 5 by conviction:
- {symbol} {direction} | Conviction {conviction}/100 | Entry {entry} | TP {tp} | SL {sl}
- Win Rate: {win_rate}% ({total_trades} trades)
- MTF: {tf_confirmation} (4H 1D 12H 1W)

### Top Movers (24H)
- Gainers: top 3
- Losers: top 3
- Volume Leaders: top 3

### Summary
2–3 sentence narrative on overall market bias and standout setups.
```

## Coin Report
Detailed view for single tickers.

```markdown
## Argus Report: {BASE} — {current time}

### Price
- Current: {ticker.price}
- Change (1H/24H/7D): {market_coins[0].change_1h}% / {market_coins[0].change_24h}% / {market_coins[0].change_7d}%
- 24H Range: {low_24h} – {high_24h}

### Oracle Signal ({micro_tf} / {macro_tf})
- Signal: {oracle.signal} | Score: {oracle.earnest.score}/4
- Bias: {oracle.bias} | State: {oracle.state}
- Advice: {oracle.advice}
- Targets: TP1 {tp1} | TP2 {tp2} | SL {sl}

### Titan Signal ({timeframe})
- Signal: {titan.signal} | Confidence: {titan.confidence}%
- Trend: {titan.trend} | Entry: {titan.entry}
- Advice: {titan.advice}

### Spot Setup
- Stance: {BUY / WAIT / AVOID} — {reason}
- Risk/Reward: {RR}:1 to TP1 | {RR}:1 to TP2

### Key Levels & Conditionals
- 🔴 Resistance: {levels}
- 🟢 Support: {levels}
- 📍 Invalidation: {levels}
```

## HODL View
*(Only for long-term intent)*

```markdown
### Long-Term / HODL View
**Macro Trend — MTF Stack:**
| Timeframe | Oracle Signal | Titan Signal |
|-----------|---------------|--------------|
| 12H       | {oracle_12h}  | {titan_1d}   |
| 1D        | {oracle_1d}   | —            |
| 1W        | {oracle_1w}   | {titan_1w}   |

**Combined Macro Verdict: {BULLISH / BEARISH / NEUTRAL}**

### Accumulation & Targets
- 🟢 Strong Acc.: {zone}
- 🔵 Deep Value: {zone}
- 🎯 Long-Term Target: {price} (+X%)
```
