# Argus Trading System — Pre-Production Audit
**Date:** 2026-04-04

---

## What You're Not Seeing

### 1. The Win Rate Illusion — 77% vs 45%

This is the single biggest red flag. The signal log shows **77.4% WR** (48W/14L), but the last 20 paper trades show **45% WR** (9W/11L). These are measuring different things:

| Metric | Signal Log (77%) | Paper Trading (45%) |
|--------|------------------|---------------------|
| Resolution | Candle-walk: did price touch TP before SL? | Real lifecycle: fill timing, expiry, slippage |
| Fill assumption | Instant at signal price | Limit order must fill within 24h |
| Capital impact | None — theoretical | Real sizing, fees, expiry cancellations |

The signal log's 77% is the **theoretical ceiling**. The paper engine's 45% is the **actual execution reality**. The gap comes from:
- **SELL_LIMIT orders expiring unfilled** — counted as neither W nor L in signal log, but they waste capital time
- **Fill slippage** — actual_entry differs from intended_entry, changing the TP/SL math
- **The batch-close problem** — 2W/6L in one batch force-closed at expiry

Backtested validated WR is **50.9%**. Paper trading at 45% means execution friction is costing ~6% WR. That's fixable.

### 2. Exposure Gate Bypassed by Race Condition

Config says `max_total_exposure_pct: 300%`. Observed exposure hit **900%** ($29,144 on $3,238 balance).

**Under normal sequential operation, the 300% cap works correctly.** The first 3x-leverage position fills the cap; the second is rejected by `check_total_exposure()`. The 900% breach happens because of a **race condition in batch signal processing:**

`execute_signals()` in `worker.py` loops through signals with `await`, but each `process_signal()` opens its own DB session (orchestrator.py:110) and queries active positions independently (line 118). When 3 signals fire in the same scan cycle, each session sees 0 active positions because prior positions haven't been committed yet (commit at line 190). All 3 pass every risk gate and create positions.

**Confirmed by code review (agent-verified):**
- `worker.py:509-544` — sequential loop, but each iteration opens fresh DB session
- `orchestrator.py:110-190` — query at line 118, commit at line 190 (72 lines of race window)
- `risk_manager.py:65-78` — exposure check uses only the in-memory `open_positions` list from line 118

**No existing test covers this scenario.** All 389 backend tests pass, but none test multi-signal batch behavior.

### 3. Position Sizing Is Too Aggressive for Prod

Current config:
```
max_position_size_pct: 10.0  (risk 10% of balance per trade)
max_leverage: 3.0            (each position = 3x notional)
max_concurrent_positions: 3  (theoretical max 9x via race condition)
max_drawdown_pct: 15.0       (circuit breaker)
```

Under normal operation (no race condition), only 1 position opens at 3x leverage before the exposure cap blocks further entries. With the race condition, 3 positions at 3x = 9x total, where a **1.7% adverse move triggers the circuit breaker**. SL distances are 2-3%, so this is within one bad candle.

The recent ADA over-concentration (4 entries, 2 stops) demonstrates this: rapid-fire entries in the same coin burned capital before the risk manager could react.

### 4. ADX Compression = Strategy Edge Evaporating

Backtest validated in a **TRENDING** market state (the primary signal driver, ~50% WR). ADX has collapsed from **52.6 to 27.9** in 14 periods. The environment is shifting to choppy/ranging where:
- SELL_LIMIT orders fill less often (price doesn't bounce to entry)
- Filled positions get whipsawed (TP/SL both close to price)
- WR will drop further

The Mar 24 report already noted ADX=15.9 "ranging/choppy." It recovered to 27.9 but is declining again. **The strategy's edge is in trends, not chop.**

### 5. Conviction Is Binary — No Signal Quality Gradient

Backtest Experiment 4 proved that conviction 55, 50, 45, and 40 all produce identical results. Every signal that passes is at 56 (the floor). There's no way to distinguish "good enough" from "excellent" setups — no mechanism to size up on better signals.

### 6. BNB Is a Persistent Drag

BNB has stopped out twice consecutively (Mar 26), backtests at 48.6% WR (one of the weakest), and is in the `btc_correlated` group competing for one of only 2 correlation slots. It's consuming a slot that TRX (61.7% WR) or DOGE (57.1% WR) could use better.

---

## Optimal Configuration

### Bear Regime (Current — BTC < EMA50)

```python
# Signal generation — VALIDATED, no changes
sl_mult = 1.5          # ATR multiplier for stop loss
tp_mult = 2.0          # ATR multiplier for take profit (fixed, no adaptive)
min_conviction = 55    # Floor (binary anyway)
block_sleeping = True  # Ignore low-vol states
block_volatile = True  # Ignore high-vol states
macro_guard = "soft"   # Regime-aligned only

# Risk management — TIGHTENED FOR PROD
max_position_size_pct = 5.0     # was 10% -> 5% risk per trade
max_leverage = 2.0              # was 3.0 -> 2.0 max notional per position
max_concurrent_positions = 3    # keep 3, but now 3 x 2x = 6x max exposure
max_total_exposure_pct = 200.0  # was 300% -> 200% (hard cap)
max_drawdown_pct = 12.0         # was 15% -> 12% (tighter circuit breaker)
max_correlated_positions = 2    # keep
order_expiry_hours = 16         # was 24h -> 16h (avoid dead capital in low vol)
```

**Why these numbers:**
- 5% risk x 3 positions = 15% max portfolio risk at any time. One stop-out = 5% drawdown. All three = 15%. Circuit breaker at 12% ensures stop before catastrophic loss.
- 2x leverage means each position is ~2x balance notional. 3 x 2x = 6x total exposure, capped at 200%.
- 16h expiry: in the current low-vol environment (ADX <30), SELL_LIMITs that don't fill in 16h probably won't fill at all.

### Bull Regime (When BTC > EMA50)

Same TP/SL parameters work — backtest validated longs at 47.7% WR vs shorts at 49.5%. The difference is small. Only change:
- Direction filter automatically flips to LONG
- Consider tightening `max_position_size_pct` to 4% for longs (slightly lower edge)

### Watchlist Optimization

Based on backtest per-coin TP=2.0x results, tier the watchlist:

| Tier | Coins | WR Range | Action |
|------|-------|----------|--------|
| **A — Always trade** | TRX, DOGE, FET, ARB | 52-62% | Full size |
| **B — Trade** | ETH, BTC, ATOM, NEAR | 49-51% | Full size |
| **C — Watch** | BNB, XRP | 46-49% | Consider removing |
| **D — Remove** | APT | 43% | Barely positive, drag |

---

## Critical Fixes Before Production

### Fix 1: Race Condition in Batch Signal Processing (P0)

The exposure gate must see positions from the current batch, not just DB state. This is the highest priority fix.

**Options (agent-verified):**
1. **In-memory accumulator** — pass a running list of batch-created positions to each `check_all()` call
2. **Sequential commit** — commit each position before processing the next signal
3. **Advisory lock** — PostgreSQL `pg_advisory_lock` around the signal batch

Option 2 is simplest: move the commit inside the loop in `worker.py:execute_signals()` or restructure `process_signal()` to commit before returning.

### Fix 2: Risk Parameters (P0)

Apply the tightened config above. The current 10%/3x/300% stack is a paper-trading config — it allowed fast growth from $1K to $3.2K but will blow up with real money.

### Fix 3: ADX Gate (P1 — Recommended)

Add an ADX threshold to the signal filter. When ADX < 20, skip signal generation entirely or reduce position size by 50%. Backtest data shows the strategy's edge lives in ADX > 25 environments.

**Feasibility (agent-verified):** ADX is calculated in Oracle but **missing from Titan** despite being referenced (`row.get('adx')` returns None). The 4H OHLCV data needed is already in memory. Implementation is ~10 lines across two files:
- Add `ta.adx()` to `titan.py:_add_indicators()` (5 lines)
- Add ADX < 20 skip logic to `signal_log.py:log_watchlist_setups()` (5 lines)

### Fix 4: Batch Race Condition Test Coverage (P1)

No existing test covers multi-signal batch behavior. Add a test that processes 3 signals in the same cycle and verifies only 1 position is created (exposure cap enforced).

---

## The Bottom Line

The system has **real edge**: 50.9% WR at 1.33 R:R = +0.185R EV per trade. That's profitable. But the gap between backtest edge (50.9%) and live execution (45%) is where money leaks out. The risk parameters are set for aggressive paper-trading growth, not capital preservation. And the exposure race condition means risk gates can be silently bypassed.

**The strategy is ready. The risk management is not.**

---

## Agent Review Summary (2026-04-04)

Four parallel agents reviewed this audit against the codebase:

| Agent | Finding | Status |
|-------|---------|--------|
| Race Condition | Confirmed at `orchestrator.py:110-190`, each `process_signal()` opens own session | **HIGH — fix required** |
| Exposure Math | 900% only via race condition; under normal operation 300% cap holds | **Corrected in audit** |
| Backend Tests | 389/389 passed, no failures; no test covers batch race scenario | **Gap identified** |
| ADX Gate | ADX missing from Titan (`row.get('adx')` → None); 10-line fix feasible | **Confirmed feasible** |

---

## Data Sources

- Backtest report: `docs/market-reports/2026-03-27-backtest-report.md` (911 signals, TP=2.0x validated)
- Market reports: Mar 24-30, Apr 4 (regime, ADX, signal track record)
- Live config: `backend/app/trading/orchestrator.py` DEFAULT_TRADING_CONFIG
- Risk manager: `backend/app/trading/risk_manager.py`
- Signal log: `backend/app/jobs/signal_log.py`
- Agent code review: `worker.py:509-544`, `orchestrator.py:105-210`, `titan.py:_add_indicators()`
