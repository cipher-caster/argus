# Trading Optimization Knowledge Base

> This file is the persistent memory for the `/optimize` slash command.
> Each optimization run appends findings here. Read this before running new sweeps.

---

## Current Best Config
Updated: 2026-03-27
- SL: 1.5x ATR | TP: 2.0x ATR (fixed, all coins) | Min Titan: 55% | Min Conviction: 50
- Gates: BLOCK_SLEEPING=T, BLOCK_VOLATILE=T, MACRO_GUARD=T, BLOCK_BTC_SELL=T
- Validated: 50.61% WR, +162.7R, 911 signals (full 11-coin watchlist, TP sweep 2026-03-27)
- Per-symbol overrides: None. `SYMBOL_OVERRIDES = {}` — BTC/ETH overrides removed after lookup bug invalidated their validation; correctly applied they degraded performance.
- **Note**: Min Conviction was previously 65, which was found to be a dead zone in confidence_sweep experiments — conf=65 produces 0 signals on the expanded 11-coin watchlist. Lowered to 50 for live production.

---

## Confirmed Rules
1. **BLOCK_SLEEPING essential** — removes noise, +8% WR improvement
2. **SOL removed** — mean-reverts on 4H, consistently negative across 7 configs
3. **Fixed TP 2.0x is the validated default** — adaptive TP and per-symbol overrides were removed after lookup bug invalidated their backtest results
4. **Soft macro guard > strict macro guard** — strict kills too many signals
5. **BNB marginal** — 40% WR, -0.7R. Monitor closely

---

## Dead Ends (Don't Re-test)
- **SL 1.0x**: stopped out too often (35.7% WR)
- **TP > 3.5x**: REVIEW pile-up, targets never reached
- **Strict macro alignment**: net negative
- **SOL on 4H trend-following**: 7 configs tested, all negative

---

## Coin Intelligence
| Coin | Signals | WR | Profit | Notes |
|------|---------|-----|--------|-------|
| BTC  | 68 | 47% | +7.7R | LONG-only in test period |
| ETH  | ~16 | 66.7% | +9.7R | Best performer, both directions |
| BNB  | ~11 | 40% | -0.7R | Marginal, keep on watchlist |

---

## Optimization Log

### 2026-03-19 — sl_sweep (full 11-coin watchlist)
- **Run ID**: e6208ea3-88eb-4f1b-b6e4-832afb8f08c5
- **Coins**: BTC, ETH, BNB, TRX, XRP, FET, NEAR, ARB, ATOM, DOGE, APT
- **Finding**: SL 1.0x has highest EV/trade (+0.225R) due to frequent small wins, but 39% WR means large drawdown exposure. SL 1.5x is safer at +0.177R EV and 48.6% WR. Lower SL = tighter stops = more trades caught = lower WR but higher absolute profit due to better RR.
- **Note**: With full 11-coin watchlist, 495 signals vs 95 previously — much more data.

| SL   | WR    | Total R  | EV/trade |
|------|-------|----------|----------|
| 1.0x | 39.0% | +109.0R  | +0.225R  |
| 1.25x| 44.7% | +101.2R  | +0.210R  |
| 1.5x | 48.6% | +85.0R   | +0.177R  |
| 1.75x| 51.8% | +71.1R   | +0.149R  |
| 2.0x | 54.2% | +57.0R   | +0.120R  |
| 2.5x | 58.6% | +39.8R   | +0.085R  |

**Decision**: Keep SL=1.5x for live trading (better WR = less drawdown, still positive EV). SL=1.0x may be better for portfolio-level backtesting but is stressful at 39% WR.

---

### 2026-03-19 — sl_sweep (run 2, updated data)
- **Run ID**: 019ae047-0d01-447a-88b6-0fc90ec2f9ff
- **Coins**: BTC, ETH, BNB, TRX, XRP, FET, NEAR, ARB, ATOM, DOGE, APT
- **Signals**: 493 (consistent across all SL values)
- **Finding**: Results consistent with prior run. SL=1.0x still has highest EV (+0.230R) but 39.1% WR. SL=1.5x remains the production sweet spot at +0.182R EV and 48.9% WR.

| SL   | WR    | Total R  | EV/trade |
|------|-------|----------|----------|
| 1.0x | 39.1% | +111.0R  | +0.230R  |
| 1.25x| 44.9% | +103.2R  | +0.215R  |
| 1.5x | 48.9% | +87.0R   | +0.182R  |
| 1.75x| 52.0% | +73.1R   | +0.154R  |
| 2.0x | 54.4% | +59.0R   | +0.124R  |
| 2.5x | 58.9% | +41.8R   | +0.089R  |

**Decision**: SL=1.5x confirmed again. No change.

---

### 2026-03-19 — confidence_sweep
- **Run ID**: d8d0c01c-6360-43a5-8d00-2a0d11012e64
- **Coins**: BTC, ETH, BNB, TRX, XRP, FET, NEAR, ARB, ATOM, DOGE, APT
- **Finding**: Confidence threshold has NO effect between 50–60. All three produce identical results (494 signals, 48.8% WR, +86.0R, +0.179R EV). At conf=65 and above, zero signals generated — the filter is too aggressive and kills all trades.
- **Conclusion**: The Oracle conviction score on this watchlist is effectively binary: most signals pass 50/55/60, and essentially none exceed 65. The current conf=65 production setting is silencing all signals on this expanded 11-coin watchlist.

| Conf | Signals | WR    | Total R  | EV/trade |
|------|---------|-------|----------|----------|
| 50   | 494     | 48.8% | +86.0R   | +0.179R  |
| 55   | 494     | 48.8% | +86.0R   | +0.179R  |
| 60   | 494     | 48.8% | +86.0R   | +0.179R  |
| 65   | 0       | N/A   | +0.0R    | N/A      |
| 70   | 0       | N/A   | +0.0R    | N/A      |
| 75   | 0       | N/A   | +0.0R    | N/A      |

**Decision**: Lower min_conviction from 65 → 55 (or 60 as a safe middle ground). The current prod setting of 65 is a dead zone — it blocks all trades.

---

### 2026-04-02 — Regime Lag Incident (Live Trade Review)

**Problem**: BTC weekly EMA50 remained in BEAR regime while BTC pumped on 4H timeframe. Hard regime gate (`signal_log.py:244-248`) forced shorts only → 9/10 trades stopped out at SL.

**Impact**: -$688.10 across 10 closed trades (1 WIN, 9 LOSS). All were SHORT positions.
- SOL SHORT: +$217.42 (+5.05%) — only winner
- Losses ranged from -$13.50 (ADA, instant SL) to -$183.87 (ADA, 30min hold)
- BTC SHORT: -$94.76, XRP: -$97.10, DOGE: -$97.97, NEAR: -$98.86, SUI: -$128.99, ATOM: -$84.80, BCH: -$105.67

**Root Cause**: Weekly EMA50 is a lagging indicator. During intra-week trend reversals, it stays in the old regime for days while 4H EMA200 (used by Titan) has already flipped. The hard gate blocks all longs in BEAR regime, so the system shorts into a rising market.

**Planned Fix (Option D — Multi-Timeframe Confirmation)**:
- Require 4H EMA200 trend (from Titan) to **agree** with weekly EMA50 regime before firing signals
- If 4H says BULLISH but weekly says BEAR → no trades (sit on hands)
- Prevents trading during regime transition periods when timeframes disagree
- Also consider a consecutive-loss circuit breaker (3-4 SL hits → auto-pause that direction)

**Monitoring**: `/regime-check` slash command created to detect this condition early.

**Decision**: Log and monitor for now. Implement Option D after backtesting against historical regime transitions.

---

*Append new runs below this line.*
