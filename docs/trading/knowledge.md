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

*Append new runs below this line.*
