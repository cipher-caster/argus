# OKX Backtest Report

**Date:** March 22, 2026
**Branch:** `feat/okx-backtesting`
**Objective:** Evaluate OKX as an alternative exchange for the Argus trading strategy, identify the best coins, and determine if the existing Binance config needs adjustment.

---

> **Data Integrity Note (2026-03-27):** This report was run while `SYMBOL_OVERRIDES` in `titan.py` contained BTC TP=4.0x and ETH TP=4.0x entries. Those overrides were never actually applied during the backtest due to a key format mismatch (`"BTC"` vs `"BTCUSDT"`). All results in this report reflect **TP=2.0x ATR for every coin** — the same as the uniform default. The overrides have since been removed. See the 2026-03-27 post-implementation audit for full details.

---

## Executive Summary

We backtested the Oracle + Titan strategy on OKX spot data across 19 coins over 8.3 months (July 2025 - March 2026). The strategy works on OKX but requires a **different coin selection** than Binance. Key finding: FET and ATOM are strong OKX-specific winners that lose money on Binance. ETH is the most reliable coin on both exchanges.

**Recommended OKX Watchlist:** ETH, FET, ATOM, STRK, BTC, XRP, POL, NEAR, DOGE

---

## Infrastructure Changes

### Code Changes Made

| File | Change |
|------|--------|
| `backend/app/trading/backtest_engine.py` | Added `provider` field to `BacktestConfig`; `load_candles()` and `load_and_prepare_data()` now filter by provider to prevent data mixing |
| `backend/scripts/backfill_history.py` | Added `--provider=` and `--symbols=` CLI flags; uses provider name from instance instead of hardcoded "binance" |
| `backend/scripts/run_signal_backtest.py` | Added `--provider=` flag passed through to config and data loader |
| `backend/scripts/okx_backtest.py` | **New file** — combined OKX backfill + backtest pipeline with pagination, `--skip-backfill`, `--sl-mult`, `--min-conv` flags |

### Test Results

- All 234 existing tests pass (backward-compatible)
- Provider isolation verified: OKX and Binance candle data are cleanly separated by `provider` column

---

## Data Overview

| Metric | Value |
|--------|-------|
| Exchange | OKX Spot |
| Time Period | July 15, 2025 - March 22, 2026 |
| Duration | 8.3 months (~250 days) |
| 4H Candles per Coin | 828-1,500 |
| 1D Candles per Coin | 139-1,500 |
| Total Candles Stored | ~50,000+ |

OKX CCXT limit: 100 candles per request. Implemented backwards pagination to accumulate 1,500 candles per symbol.

---

## Part 1: OKX Coin Screening

### Batch 1 — Original Watchlist + New Candidates (11 coins)

| Coin | Signals | WR | P/L | Verdict |
|------|---------|-----|------|---------|
| **ETH** | 19 | 68.4% | +12.7R | **Best** |
| BTC | 15 | 60.0% | +7.3R | Solid |
| LINK | 25 | 45.8% | +2.3R | Decent |
| AVAX | 32 | 45.2% | +1.7R | Marginal |
| DOT | 33 | 43.8% | +1.3R | Marginal |
| HYPE | 13 | 46.2% | +1.0R | Small sample |
| ADA | 30 | 41.4% | -0.3R | Flat |

### Batch 2 — Extended Screening (12 coins)

| Coin | Signals | WR | P/L | Verdict |
|------|---------|-----|------|---------|
| **FET** | 27 | 61.5% | +12.7R | **OKX winner** |
| **ATOM** | 32 | 58.1% | +12.3R | **OKX winner** |
| XRP | 17 | 56.2% | +5.7R | Solid |
| NEAR | 29 | 48.3% | +6.3R | Decent |
| SOL | 24 | 47.8% | +4.0R | Decent |
| DOGE | 26 | 48.0% | +3.7R | Decent |
| ARB | 28 | 42.3% | +1.0R | Marginal |
| BNB | 19 | 43.8% | +0.3R | Marginal |
| RENDER | 31 | 41.9% | 0.0R | Flat |
| INJ | 32 | 36.7% | -3.7R | **Loser** |
| SUI | 25 | 39.1% | -1.3R | **Loser** |

### Batch 3 — ETH Ecosystem Coins (8 coins)

| Coin | Signals | WR | P/L | Verdict |
|------|---------|-----|------|---------|
| **STRK** | 27 | 57.7% | +11.0R | **ETH L2 winner** |
| **POL** | 30 | 53.6% | +7.7R | **Good** |
| LDO | 32 | 50.0% | +5.3R | Decent |
| OP | 27 | 46.2% | +3.3R | Marginal |
| ZK | 39 | 43.6% | +1.3R | Marginal |
| ARB | 28 | 42.3% | +1.0R | Marginal |
| ENS | 34 | 35.3% | -6.0R | **Bad** |
| METIS | 25 | 25.0% | -9.3R | **Worst** |

---

## Part 2: Binance vs OKX Comparison

Same coins, same strategy, different exchanges:

| Coin | Binance WR | Binance P/L | OKX WR | OKX P/L | Verdict |
|------|-----------|-------------|--------|---------|---------|
| **ETH** | 61.9% | +10.7R | 68.4% | +12.7R | **Consistent winner both** |
| **XRP** | 53.2% | +22.3R | 56.2% | +5.7R | **Consistent both** |
| BTC | 47.1% | +14.0R | 60.0% | +7.3R | Decent both |
| DOGE | 47.4% | +9.3R | 48.0% | +3.7R | Decent both |
| NEAR | 46.2% | +9.7R | 48.3% | +6.3R | Decent both |
| **FET** | 42.0% | -0.3R | 61.5% | **+12.7R** | **OKX only** |
| **ATOM** | 41.2% | -2.7R | 58.1% | **+12.3R** | **OKX only** |
| HYPE | 66.7% | +3.3R | 46.2% | +1.0R | Binance better (small sample) |
| **SOL** | 32.4% | **-7.7R** | 47.8% | +4.0R | **Avoid on Binance** |

### Key Differences

- **FET and ATOM** lose money on Binance but are top performers on OKX. Different exchange liquidity profiles create different price behavior.
- **ETH** is the most consistent coin across both exchanges — high WR, positive P/L.
- **SOL** is terrible on Binance but viable on OKX.
- **XRP** is strong on both, with higher total R on Binance (longer data history).
- **Shorts outperform longs on OKX** (51.5% WR vs 41.8% WR). On Binance, more balanced.

---

## Part 3: Parameter Sweeps

### Stop-Loss Sweep (OKX Data, 7 Coins)

| SL Multiplier | Signals | WR | Total R | EV/trade | Notes |
|--------------|---------|-----|---------|----------|-------|
| **1.0x** | 165 | 45.1% | +69.0R | **+0.426R** | Best EV, aggressive |
| 1.25x | 165 | 51.2% | +63.4R | +0.391R | |
| **1.75x** | 165 | 62.7% | +63.3R | +0.401R | Best balance |
| 1.5x (current) | 165 | 56.5% | +60.7R | +0.377R | Middle ground |
| 2.0x | 165 | 66.2% | +59.5R | +0.379R | |
| 2.5x | 165 | 66.9% | +39.2R | +0.250R | Worst EV |

**Binance SL sweep (for comparison):**

| SL Multiplier | Signals | WR | Total R | EV/trade |
|--------------|---------|-----|---------|----------|
| 1.0x | 506 | 38.4% | +103.0R | +0.207R |
| 1.25x | 506 | 44.1% | +96.8R | +0.196R |
| 1.5x (current) | 506 | 48.6% | +87.3R | +0.177R |
| 1.75x | 506 | 51.8% | +74.3R | +0.152R |
| 2.0x | 506 | 54.0% | +57.0R | +0.117R |
| 2.5x | 506 | 58.3% | +38.4R | +0.079R |

**Conclusion:** SL=1.0x gives best EV on both exchanges. Current SL=1.5x is a reasonable middle ground. SL=1.75x is worth considering for OKX specifically (higher WR at similar EV).

### Confidence Sweep (OKX Data)

| Min Confidence | Signals | WR | P/L |
|---------------|---------|-----|------|
| 50% | 165 | 56.5% | +60.7R |
| 55% (current) | 165 | 56.5% | +60.7R |
| 60% | 165 | 56.5% | +60.7R |
| 65% | 0 | — | — |
| 70% | 0 | — | — |
| 75% | 0 | — | — |

**Conclusion:** Binary filter. All signals have Titan confidence 55-64%. Current 55% threshold is optimal — any higher kills all signals. Not a useful tuning lever.

---

## Part 4: Market State Analysis

| Market State | OKX WR | Binance WR | Recommendation |
|-------------|--------|------------|----------------|
| **TRENDING** | ~58% | ~52% | **Trade this** |
| SLEEPING | ~40% | ~45% | Block or avoid |
| **SUPER TREND** | **~11%** | **~16%** | **Never trade — trap** |
| VOLATILE | N/A (blocked) | N/A (blocked) | Keep blocking |

SUPER TREND is consistently the worst regime across both exchanges. The block_sleeping and block_volatile flags should remain enabled.

---

## Final Recommendations

### OKX Watchlist (9 Coins)

| Rank | Coin | OKX WR | OKX P/L | Why |
|------|------|--------|---------|-----|
| 1 | **ETH** | 68.4% | +12.7R | Most reliable, works on both exchanges |
| 2 | **FET** | 61.5% | +12.7R | OKX-specific winner |
| 3 | **ATOM** | 58.1% | +12.3R | OKX-specific winner |
| 4 | **STRK** | 57.7% | +11.0R | ETH L2, follows ETH pattern |
| 5 | **BTC** | 60.0% | +7.3R | Market gate + signals |
| 6 | **XRP** | 56.2% | +5.7R | Consistent across exchanges |
| 7 | **POL** | 53.6% | +7.7R | ETH scaling, good WR |
| 8 | **NEAR** | 48.3% | +6.3R | Solid L1 |
| 9 | **DOGE** | 48.0% | +3.7R | Meme momentum |

### Coins to Avoid on OKX

| Coin | OKX WR | OKX P/L | Reason |
|------|--------|---------|--------|
| METIS | 25.0% | -9.3R | Worst performer |
| ENS | 35.3% | -6.0R | Consistent loser |
| INJ | 36.7% | -3.7R | Negative EV |
| SUI | 39.1% | -1.3R | Negative EV |
| RENDER | 41.9% | 0.0R | Flat, not worth the risk |

### Configuration

**Keep current Binance config for OKX — no changes needed:**
- SL=1.5x ATR (or try 1.75x for OKX if you want higher WR)
- TP=2.0x ATR fixed (default as of 2026-03-27; adaptive TP was removed)
- Min Titan confidence=55%
- Soft macro guard=ON
- Block SLEEPING=ON
- Block VOLATILE=ON

### Exchange-Specific Strategy

| | Binance | OKX |
|---|---------|-----|
| **Best coins** | ETH, XRP, BTC, DOGE, NEAR | ETH, FET, ATOM, STRK, BTC |
| **Unique winners** | XRP (highest R) | FET, ATOM, STRK |
| **Avoid** | SOL | INJ, SUI, ENS, METIS |
| **Config** | SL=1.5x, conf=55% | Same |

**Do not copy-paste the watchlist between exchanges.** Each exchange has different liquidity and order flow. FET/ATOM are the clearest example of exchange-specific behavior.

---

## Next Steps

1. Deploy OKX watchlist to worker config via Redis
2. Monitor live performance for 2-4 weeks before committing capital
3. Consider testing SL=1.75x on OKX for higher WR if 45% feels too low
4. Evaluate ETH ecosystem coins (STRK, POL) for Binance — may behave differently there
5. Re-run OKX backtest quarterly to catch regime changes

---

## Appendix: Raw Backtest Output

### OKX Overall Stats (All 19 Coins Combined)

- **Total signals:** 597
- **Win Rate:** 47.5%
- **Total Profit:** +77.3R
- **Avg R:R:** 1.51:1
- **Longs:** 41.8% WR
- **Shorts:** 51.5% WR

### Binance Overall Stats (9 Comparable Coins)

- **Total signals:** 590
- **Win Rate:** 46.1%
- **Total Profit:** +58.7R
- **Avg R:R:** 1.41:1
- **Longs:** 45.4% WR
- **Shorts:** 47.1% WR

OKX produces slightly better results overall, driven primarily by FET, ATOM, and STRK which are strong OKX-specific performers.
