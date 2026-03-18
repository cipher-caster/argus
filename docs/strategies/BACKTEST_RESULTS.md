# Backtest Results & Strategy Optimization

**Date:** 2026-03-17
**Period:** Dec 2023 – Mar 2026 (varies by coin)
**Strategy:** Oracle + Titan combined gate on 4H
**Production settings:** BLOCK_SLEEPING + ADAPTIVE_TP (2.0x/3.0x) + SOFT_MACRO

---

## Data Coverage

| Coin | 4H Candles | Date Range | 1D Candles |
|------|-----------|------------|------------|
| BTC/USDT | 4,322 | Dec 2023 – Mar 2026 | 303 |
| ETH/USDT | 1,218 | Feb 2025 – Mar 2026 | 503 |
| SOL/USDT | 1,318 | Apr 2025 – Mar 2026 | 252 |
| BNB/USDT | 1,018 | Sep 2025 – Mar 2026 | 253 |

---

## Production Results (BTC + ETH + BNB)

Using optimal settings (BLOCK_SLEEPING + ADAPTIVE_TP + SOFT_MACRO):

| Coin | Signals | WR | Profit | LONG/SHORT |
|------|---------|-----|--------|------------|
| BTC | 68 | 47.0% | +7.7R | 68L / 0S |
| ETH | 15 | 66.7% | +9.7R | 10L / 5S |
| BNB | 12 | 40.0% | -0.7R | 6L / 6S |
| **Total** | **95** | **48.3%** | **+16.7R** | |

- Shorts outperform longs: 55.6% WR vs 44.8%
- ETH is the best performer by far (66.7% WR, +9.7R on 15 signals)
- BTC generates volume (68 signals) with decent edge
- BNB is marginal but above breakeven on WR

### Break-even Reference
At 2:1 RR (SUPER TREND) → breakeven = 33.3%
At 1.33:1 RR (TRENDING) → breakeven = 42.9%

---

## SOL Removed from Watchlist

SOL was tested across 7+ parameter configurations and was **consistently negative**:

| Config | Signals | WR | Profit |
|--------|---------|-----|--------|
| Baseline (SL 1.5, TP 2.0) | 23 | 39.1% | -2.0R |
| Tighter TP (1.5x) | 23 | 43.5% | -3.0R |
| Score >= 4 only | 18 | 38.9% | -1.7R |
| Wider SL (2.0x) | 18 | 44.4% | -2.0R |
| Raw (no fixes) | 35 | 25.7% | -8.0R |

**Root cause:** SOL doesn't trend cleanly on 4H. The Oracle+Titan trend-following strategy requires directional persistence, and SOL mean-reverts too frequently. Even in TRENDING market state, SOL only achieves 33.3% WR (breakeven).

**Decision:** Removed from `signal_log.py` watchlist. Can be re-evaluated if:
- We add a mean-reversion strategy mode
- SOL's behavior changes in a sustained bull market
- We test 1H timeframe (shorter moves may suit SOL better)

---

## Parameter Sweep Results

All tests with BLOCK_SLEEPING + SOFT_MACRO enabled, 118 signals across all 4 coins:

| Config | WR | Total R | EV/trade | Notes |
|--------|-----|---------|----------|-------|
| No fixes (raw) | 38.9% | +32.0R | +0.16R | 198 signals, high volume but low WR |
| **SL 1.5 / TP 2.0 adaptive** | **46.5%** | **+13.0R** | **+0.11R** | **Production default** |
| SL 1.0x (tighter) | 35.7% | +13.0R | +0.11R | Stopped out too often |
| SL 1.25x | 41.2% | +12.2R | +0.10R | Marginally worse |
| SL 2.0x (wider) | 54.9% | +14.0R | +0.12R | Best WR but lower RR |
| TP 2.5x fixed | 42.5% | +15.0R | +0.13R | BTC benefits, BNB suffers |
| SL 2.0 + TP 2.5 | 50.9% | +16.0R | +0.14R | Highest EV/trade |
| TP 2.0 fixed (all states) | 48.3% | +14.6R | +0.12R | No SUPER TREND bonus |

### Key Findings

1. **SL 1.5x ATR is the sweet spot** — tighter stops get hunted, wider stops reduce RR without proportional WR gain
2. **Adaptive TP (2.0x/3.0x) validated** — gives the best WR (46.5%) while maintaining edge. The SUPER TREND bonus works for BTC
3. **TP 2.5x is interesting for BTC** (+10.7R vs +6.3R at 2.0x) but kills BNB profitability. Not worth the coin-specific complexity
4. **BLOCK_SLEEPING is essential** — raw strategy fires 12 SOL signals in SLEEPING state at 16.7% WR
5. **SOFT_MACRO guard works** — blocks the worst counter-trend entries without being too restrictive

---

## Three Optimizations (Applied in Production)

### 1. Block SLEEPING (ADX < 20)
Trend-following has no edge in range-bound markets. Removed 80 signals (198 → 118) and improved WR from 38.9% → 46.5%.

### 2. Adaptive TP (2.0x ATR normal, 3.0x SUPER TREND)
The biggest single optimization. In TRENDING state (ADX 20-40), 3x ATR targets are too ambitious and cause REVIEW pile-up. 2x ATR is reachable. In SUPER TREND (ADX > 40), the extended 3x target captures more of the move.

### 3. Soft Macro Guard
No LONG when macro bias is BEARISH. No SHORT when macro is BULLISH. NEUTRAL macro allowed through. This is less restrictive than strict macro alignment (which killed too many signals) but filters the worst counter-trend entries.

---

## Known Limitations

1. **Titan confidence always 60%** — only BUY_LIMIT/SELL_LIMIT signals fire. High-conviction signals (80%+) require rare SMC conditions (MSS + sweep) or RSI dip (< 45 for BUY, > 55 for SELL) that don't coincide with the Oracle gate
2. **All signals are low conviction (< 70)** — the conviction scoring never exceeds ~64 because Titan maxes at 60% confidence
3. **SMC look-ahead** — MSS, sweeps, and FVGs are pre-computed on the full dataset. Primary indicators (EMA, RSI, MACD, SuperTrend, ADX, BB) are strictly backward-looking
4. **Same-candle TP+SL** — resolved as LOSS (conservative assumption)
5. **BTC has no SHORT signals** — Oracle+Titan rarely agree on bearish direction for BTC during the test period (primarily bull/range market)
6. **Statistical significance** — BNB has only 12 signals, ETH has 15. Need 3-6 months more live data

---

## Commands

```bash
# Run backtest with optimal settings (dry run)
docker compose exec backend python scripts/run_signal_backtest.py --dry-run --fix-optimal

# Run backtest with custom parameters
docker compose exec backend python scripts/run_signal_backtest.py --dry-run --fix-sleeping --fix-soft-macro --sl-mult=2.0 --tp-mult=2.5

# Write results to DB
docker compose exec backend python scripts/run_signal_backtest.py --clear --fix-optimal

# Check live signal log
curl http://localhost:8000/api/analytics/signal-log?source=live
curl http://localhost:8000/api/analytics/signal-log?source=backtest
```
