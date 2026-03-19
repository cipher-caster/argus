# Argus Report Templates

## Market Report
Generate via parallelizing all pulse endpoints.

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
List the top 5 by absolute score:
- {symbol} | Score {score} | {bias} | {state} | {opportunity}

### Best Setups (4H — Oracle + Titan Confluence)
List top 5 by conviction:
- {symbol} {direction} | Conviction {conviction}/100 | Entry {entry} | TP {tp} | SL {sl}
- Win Rate: {win_rate}% ({total_trades} trades)
- MTF: {4H, 1D, 12H, 1W checkmarks}

### Top Movers (24H)
- Gainers: top 3 | Losers: top 3 | Volume Leaders: top 3

### Summary
2–3 sentence narrative on overall market bias and standout setups.
```

## Coin Report
Detailed view for single tickers.

```markdown
## Argus Report: {BASE} — {current time}

### Price
- Current: {ticker.price}
- 1H Change: {change_1h}% | 24H Change: {change_24h}% | 7D Change: {change_7d}%
- 24H Range: {low_24h} – {high_24h} | Volume (24H): {volume_24h}

### Oracle Signal ({micro_tf} / {macro_tf})
- Signal: {oracle.signal} | Score: {oracle.earnest.score}/4
- Bias: {oracle.bias} | State: {oracle.state}
- Advice: {oracle.advice}
- Targets: TP1 {tp1} | TP2 {tp2} | SL {sl}

### Titan Signal ({timeframe})
- Signal: {titan.signal} | Confidence: {titan.confidence}%
- Trend: {titan.trend} | Entry: {titan.entry} | TP: {tp} | SL: {sl}
- Advice: {titan.advice}

### Spot Setup
- Stance: {BUY / WAIT / AVOID} — {reason}
| Level | Price | Notes |
|-------|-------|-------|
| Entry | $X | {market / limit} |
| TP1   | $X | {+X% — target} |
| Cut Loss | $X | {-X% — stop} |
- Risk/Reward: {RR}:1 to TP1 | {RR}:1 to TP2

### Key Levels & What to Watch
- 🔴 Resistance: {EMA20, Swing High}
- 🟢 Support: {EMA50, SuperTrend}
- 📍 Invalidation: {Bull/Bear cases}

### Long-Term / HODL View
*(Only if long_term_mode = true)*
- Macro Verdict: **{BULLISH / BEARISH / NEUTRAL}**
- 🟢 Strong Accumulation: {zone}
- 🎯 Long-Term Target: {price} (+X%)
- Verdict: {ACCUMULATE / WAIT / AVOID}
```

## Backtest Results
Output from `run_signal_backtest.py`.

```markdown
## Backtest Results: {COINS} (4H, Optimized)

### Summary
- Total Signals: {N} | Win Rate: {X}% ({W}W / {L}L / {R}R)
- Total Profit: {X}R | Avg Risk/Reward: {X}:1

### Per-Coin Breakdown
- **{COIN}**: {N} signals | {WR}% WR | {profit}R profit

### Verdict
- **{ADD TO WATCHLIST / MARGINAL / SKIP}**
- Reasoning: {one sentence based on WR and total profit}
```

## Portfolio Report
Output from `/api/trading/portfolio`.

```markdown
## Argus Portfolio — {today's date}

### Balance
- Unrealized: **${unrealized_pnl:+.2f}** | Total Equity: **${total_equity}**
- Exposure: {exposure_pct}% of balance

### Open Positions ({count})
- {SYMBOL} {LONG/SHORT} | Entry **${entry}** → Now **${price}** | PnL **{pnl_pct}%**

### Trade Intelligence
- Best coin: {symbol} ({WR}%) | Worst coin: {symbol} ({WR}%)
- Conviction sweet spot: {bucket}% | Market state edge: {state}
```
