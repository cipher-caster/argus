# Trading Optimization Knowledge Base

> This file is the persistent memory for the `/optimize` slash command.
> Each optimization run appends findings here. Read this before running new sweeps.

---

## Current Best Config
Updated: 2026-03-17
- SL: 1.5x ATR | TP: adaptive 2.0/3.0 | Min Titan: 55% | Min Conviction: 65
- Gates: BLOCK_SLEEPING=T, BLOCK_VOLATILE=T, MACRO_GUARD=T, BLOCK_BTC_SELL=T
- Expected: 48.3% WR, +16.7R, ~0.18R EV/trade on 95 signals (BTC+ETH+BNB)

---

## Confirmed Rules
1. **BLOCK_SLEEPING essential** — removes noise, +8% WR improvement
2. **SOL removed** — mean-reverts on 4H, consistently negative across 7 configs
3. **Adaptive TP (2.0/3.0) outperforms fixed TP for BTC**
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

*Append new runs below this line.*
