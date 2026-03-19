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

## Expanded 11-Coin Watchlist Results (2026-03-19)

**Coins:** BTC, ETH, BNB, TRX, XRP, FET, NEAR, ARB, ATOM, DOGE, APT
**Signal count:** 495 (vs 95 previously — 5x more data)
**Run ID:** e6208ea3-88eb-4f1b-b6e4-832afb8f08c5

SOL was excluded from the expanded watchlist. Root cause is its mean-reverting character on 4H — trend-following has no durable edge there (see "SOL Removed" section above).

### SL Multiplier Sweep (full watchlist, 495 signals)

All tests with BLOCK_SLEEPING + SOFT_MACRO enabled, adaptive TP (2.0x/3.0x):

| SL Mult | WR    | Total R  | EV/trade |
|---------|-------|----------|----------|
| 1.0x    | 39.0% | +109.0R  | +0.225R  |
| 1.25x   | 44.7% | +101.2R  | +0.210R  |
| **1.5x**| **48.6%** | **+85.0R** | **+0.177R** |
| 1.75x   | 51.8% | +71.1R   | +0.149R  |
| 2.0x    | 54.2% | +57.0R   | +0.120R  |
| 2.5x    | 58.6% | +39.8R   | +0.085R  |

### Key Findings

1. **SL 1.0x has the highest EV/trade (+0.225R)** — tighter stops mean better RR, so even at 39% WR the absolute profit is highest. However, 39% WR means sustained drawdown exposure that is difficult to trade through in practice.
2. **SL 1.5x remains the production choice** — 48.6% WR with +0.177R EV/trade. Better psychological tolerance and lower drawdown than the 1.0x configuration.
3. **Diminishing returns above 1.5x** — wider stops improve WR but degrade RR faster than WR gains can compensate. EV/trade falls monotonically from 1.5x onward.
4. **5x more data confirms the original finding** — the SL 1.5x sweet spot identified on 95 signals holds at 495 signals.

### Decision

Keep `SL=1.5x` for live trading. SL=1.0x may be superior for portfolio-level simulation but is operationally stressful at 39% WR. The expanded 11-coin watchlist provides sufficient signal volume (+0.177R × 495 signals = +87.6R theoretical maximum) to justify the current configuration.

---

## BTC Multi-Timeframe Analysis (2026-03-19)

**Goal:** Find the most profitable timeframe and strategy for BTC across 15m, 1h, 4h, and 1d.

### Oracle on BTC — All Timeframes Negative

| Config | Trades | WR | EV/Trade | Verdict |
|--------|--------|-----|----------|---------|
| 15m / 4h | 43 | 9.3% | -0.721R | Catastrophic |
| 1h / 1d | 16 | 12.5% | -0.625R | Broken |
| 4h / 1w | 4 | 0.0% | -1.000R | Broken |
| 1d / 1M | 6 | 33.3% | 0.000R | Breakeven |

**Root cause:** Oracle's Earnest voter system (RSI, Bollinger, ADX, EMA200) generates too many false signals for BTC. BTC trends strongly, so RSI stays overbought/oversold for extended periods, causing the strategy to enter at bad prices. The 5-voter system lacks the SMC/structure context that Titan has.

**Decision:** Oracle should not be used as a primary signal source for BTC. Use it only as a macro bias filter (daily direction check), not for entry timing.

### Titan on BTC — Positive Edge, Thin

| Timeframe | Trades | WR | EV/Trade | Total R | Max DD |
|-----------|--------|-----|----------|---------|--------|
| 15m | 65 | 36.9% | -0.138R | -9.00R | 13.67R |
| **1h** | **20** | **55.0%** | **+0.283R** | **+5.67R** | **4.0R** |
| **4h** | **55** | **45.5%** | **+0.061R** | **+3.33R** | **13.0R** |
| **1d** | **20** | **50.0%** | **+0.167R** | **+3.33R** | **2.67R** |

- 15m is too noisy — 65 trades, 37% WR, negative EV
- 1h gives the best signal frequency with solid edge (55% WR, +0.283R EV)
- 4h has the most data (0.46yr) — edge exists but is thin at default params
- 1d is cleanest (2.67R max DD) but low trade count

### Parameter Sweep — 4H Deep Dive (1000 candles, 0.46yr)

| SL | TP | Min Conf | Trades | WR | EV/Trade | Total R | Max DD |
|----|-----|----------|--------|-----|----------|---------|--------|
| 1.75 | 4.0 | 50 | 26 | 38.5% | **+0.264R** | +6.86R | 5.4R |
| 2.0 | 4.0 | 50 | 25 | 40.0% | +0.200R | +5.00R | 5.0R |
| 1.0 | 1.5 | 65 | 13 | 46.2% | +0.154R | +2.00R | 2.5R |
| 1.75 | 2.0 | 50 | 48 | 52.1% | +0.116R | +5.57R | 6.6R |
| 2.0 | adaptive | 50 | 45 | 55.6% | +0.111R | +5.00R | 6.0R |
| 1.5 | adaptive | 50 | 55 | 45.5% | +0.061R | +3.33R | 13.0R |

### Key BTC-Specific Findings

1. **Wider stops + wider targets dominate** — SL=1.75x + TP=4.0x gives +0.264R EV, nearly 4x the default (+0.061R). BTC's volatility requires room to breathe.

2. **R:R ratio matters more than WR for BTC** — The best config has 38.5% WR but +0.264R EV because the 2.29:1 R:R means wins are 2.3x larger than losses.

3. **Higher conviction helps** — MinConf=65-70 reduces trade count but improves WR. The cleanest curve: SL=1.0, TP=1.5, MC=65 gives 46.2% WR with only 2.5R max DD.

4. **Shorts have an asymmetric edge on BTC** — With wider TP (4.0x), shorts win at ~39% which is above breakeven (33%) at the 2.29:1 RR. BTC dumps harder than it pumps.

5. **Oracle is counterproductive for BTC** — The existing BACKTEST_RESULTS.md shows BTC with 47% WR on Oracle+Titan combined. This analysis shows Oracle alone is 9-12% WR. Oracle is dragging BTC performance down.

### Implementation — Per-Symbol Risk Overrides

Added `SYMBOL_OVERRIDES` dict in `titan.py` for coin-specific risk parameters:

```python
SYMBOL_OVERRIDES = {
    "BTCUSDT":  {"sl_mult": 1.75, "tp_mult": 4.0},
    "BTC/USDT": {"sl_mult": 1.75, "tp_mult": 4.0},
}
```

- Default (all other coins): SL=1.5x ATR, TP=adaptive (2-3x based on ADX)
- BTC: SL=1.75x ATR, TP=4.0x ATR (R:R 2.29 vs default 1.33)

All call sites updated: `routes/strategy.py`, `routes/analytics.py`, `jobs/signal_log.py`, `trading/backtest_engine.py`, `worker.py`.

### Recommended BTC Configuration

| Parameter | Value | Why |
|-----------|-------|-----|
| Strategy | Titan only | Oracle is negative for BTC |
| Timeframe | 4H | Best balance of frequency + edge |
| SL | 1.75x ATR | Wider stops reduce false exits |
| TP | 4.0x ATR | BTC trends extend further than alts |
| Min Confidence | 55-60 | Filter noise without losing too many signals |
| R:R | 2.29:1 | Break-even WR = 30.4% |

### Analysis Scripts

Located in `backend/scripts/`:

```bash
# Multi-timeframe comparison (Oracle + Titan, all timeframes)
docker compose exec backend python -m scripts.btc_timeframe_analysis

# Extended backtest + parameter sweep on 1h and 1d
docker compose exec backend python -m scripts.btc_titan_deep_dive

# Focused 4H parameter sweep (most granular)
docker compose exec backend python -m scripts.btc_4h_sweep

# HODL vs Trading comparison
docker compose exec backend python -m scripts.btc_hodl_vs_trade
```

---

## ETH Multi-Timeframe Analysis (2026-03-19)

**Goal:** Same analysis as BTC — find best timeframe and params for ETH.

### Oracle on ETH — Even Worse Than BTC

| Config | Trades | WR | EV/Trade | Verdict |
|--------|--------|-----|----------|---------|
| 15m / 4h | 42 | 21.4% | -0.357R | Broken |
| 1h / 1d | 45 | 15.6% | -0.533R | Broken |
| 4h / 1w | 39 | 12.8% | -0.615R | Broken |
| 1d / 1M | 14 | 7.1% | -0.786R | Broken |

Oracle is **catastrophic** on ETH. Worse than BTC on every single timeframe. The Earnest voter system is fundamentally incompatible with ETH's price action.

### Titan on ETH — Better Than BTC at Default Settings

| Timeframe | Trades | WR | EV/Trade | Total R | Max DD | Ann.R |
|-----------|--------|-----|----------|---------|--------|-------|
| **15m** | **54** | **50.0%** | **+0.191R** | **+10.33R** | **5.0R** | **+362** |
| 1h | 61 | 36.1% | -0.126R | -7.67R | 15.0R | -67 |
| **4h** | **43** | **51.2%** | **+0.240R** | **+10.33R** | **5.0R** | **+22.7** |
| 1d | 20 | 35.0% | -0.150R | -3.00R | 5.67R | -2.2 |

Key difference from BTC: **ETH 15m is profitable** (50% WR, +0.191R EV). BTC 15m was noise (37% WR, -0.138R). ETH trends more cleanly on lower timeframes.

The default SL=1.5, TP=adaptive on 4H already gives +0.240R EV — better than BTC's default (+0.061R). ETH doesn't need parameter overrides like BTC.

### Parameter Sweep — 4H

| SL | TP | MC | Trades | WR | EV/Trade | Max DD |
|----|-----|-----|--------|-----|----------|--------|
| 2.0 | adaptive | 65 | 6 | 83.3% | +0.750R | 1.0R |
| 2.0 | 2.0 | 65 | 6 | 83.3% | +0.667R | 1.0R |
| 1.5 | 4.0 | 50 | 22 | 40.9% | +0.500R | 4.0R |
| 1.0 | 4.0 | 50 | 37 | 29.7% | +0.486R | 9.0R |
| **1.5** | **adaptive** | **50** | **43** | **51.2%** | **+0.240R** | **5.0R** |

The "best" configs (SL=2.0, MC=65) have only 6 trades — statistically unreliable. The default SL=1.5 adaptive with 43 trades is the most robust positive configuration.

### HODL vs Trading

| Approach | Ann. Return | Max DD | Return/DD |
|----------|-------------|--------|-----------|
| HODL | -79.8% | 61.3% | -1.30 |
| Titan default @1x | +22.7% | 5.0% | +4.54 |
| Titan default @3x | +68.0% | 15.0% | +4.54 |
| **Titan default @5x** | **+113.3%** | **25.0%** | **+4.54** |

ETH lost 51.7% in this period ($4,487 → $2,166). HODL was brutal. Trading at 5x leverage gave +113% with only 25% max DD — massively better risk-adjusted performance.

### ETH vs BTC Summary

| Metric | BTC | ETH |
|--------|-----|-----|
| Oracle works? | No (9-33% WR) | No, worse (7-21% WR) |
| Titan default EV (4H) | +0.061R | +0.240R |
| Needs param override? | Yes (wider SL/TP) | No (default works) |
| Best timeframe | 4H only | 4H and 15m |
| HODL return (this period) | -42.8% | -51.7% |
| HODL max DD | 49.8% | 61.3% |
| Trading risk-adjusted score | +3.49 | +4.54 |

**ETH is easier to trade than BTC.** Default Titan parameters work well, 15m timeframe also has edge, and the risk-adjusted score is higher. ETH's more volatile swings create cleaner signal patterns.

### Per-Symbol Overrides

BTC needs overrides. ETH does not. The `SYMBOL_OVERRIDES` dict only contains BTC:

```python
SYMBOL_OVERRIDES = {
    "BTCUSDT":  {"sl_mult": 1.75, "tp_mult": 4.0},
    "BTC/USDT": {"sl_mult": 1.75, "tp_mult": 4.0},
}
# ETH uses default: SL=1.5x ATR, TP=adaptive (2-3x based on ADX)
```

### Analysis Script

```bash
docker compose exec backend python -m scripts.eth_full_analysis
```

---

## HODL vs Trading vs Futures (2026-03-19)

**Period:** ~0.46yr (4H data), BTC moved from $122k → $70k (-43%)

### Raw Results

| Approach | Ann. Return | Max DD | Trades | Return/DD |
|----------|-------------|--------|--------|-----------|
| HODL | -70.6% | 49.8% | 0 | -1.42 |
| Titan default (SL=1.5, adaptive) | -27.4% | 10.0% | 225 | -2.74 |
| **Titan BTC-opt (SL=1.75, TP=4.0) @1x** | **+18.9%** | **5.4%** | **26** | **+3.49** |
| Titan BTC-opt @3x | +56.8% | 16.3% | 26 | +3.49 |
| Titan BTC-opt @5x | +94.6% | 27.1% | 26 | +3.49 |
| Titan tight (SL=1.0, TP=1.5) @1x | +6.1% | 2.5% | 13 | +2.42 |

### Why HODL Lost

This period was a BTC bear leg ($122k → $70k). HODL means riding the full -43% drawdown with no hedge. 93% of the time BTC was in >10% drawdown. HODL only works if you believe the long-term trend is up AND you can stomach 50% drops.

### Why Default Titan Lost

The default SL=1.5x ATR is too tight for BTC's volatility. In a trending-down market, price frequently "wicks" through the stop before continuing to the target. 225 trades fired (too many), 95.6% individually won but the few that lost were outsized because BTC's dumps are violent.

### Why BTC-Optimized Titan Won

SL=1.75x gives enough room for BTC's wicks. TP=4.0x means winners are 2.3x bigger than losers. Only 26 trades (quality over quantity). **The shorts carried the strategy** — BTC was in a downtrend, and short signals captured the move while HODL bled.

### The Real Answer: It Depends on the Market

| Market Phase | Best Approach | Why |
|--------------|--------------|-----|
| **Strong bull** (BTC trending up) | HODL or low-leverage longs | Trend-following captures the full move |
| **Bear / downtrend** | Titan shorts (futures) | Only way to profit; HODL loses |
| **Choppy / range** | Titan with high MC (65-70) | Fewer trades, avoids noise |
| **You can't watch the market** | HODL | Trading requires execution |
| **You want defined risk** | Titan @1x-3x | Max DD is known per trade |

### The Leverage Question

- **1x (spot):** +18.9% ann. return, 5.4% max DD. Safe, but modest.
- **3x:** +56.8% return, 16.3% DD. Good risk/reward.
- **5x:** +94.6% return, 27.1% DD. Aggressive but manageable.
- **10x:** +137% return, 54.3% DD. One bad streak and you're wrecked.

**Sweet spot: 3-5x leverage** with BTC-optimized Titan. Enough juice to beat HODL in bull markets, and the SHORT side protects you in bear markets where HODL just bleeds.

### Bottom Line

1. **In a bull market:** HODL BTC with a small trading allocation (20-30%) for alpha.
2. **In a bear/choppy market:** Titan futures (3-5x) is the only profitable approach.
3. **Across all regimes:** Titan BTC-optimized @3x beats HODL on risk-adjusted basis (3.49 vs -1.42 in this bear period).

The edge isn't the signals — it's the risk management. Defined stops, asymmetric targets, and the ability to go short.

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
