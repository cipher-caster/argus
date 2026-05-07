---
name: Strategy performance findings and regime detection
description: Oracle deprecated from UI, regime detection system active, Titan is primary strategy with per-symbol overrides, expanded backtest results
type: project
originSessionId: e8dc91a7-8713-485f-bd3f-8e7acb71133b
---
**Regime Detection System (shipped 2026-03-19, merged to master):**
- Oracle removed from all UI — backend code preserved for future experiments
- BTC weekly EMA50 regime detection replaces Oracle market gate
- `GET /api/strategy/regime` — cached 1hr, returns BULL/BEAR/UNKNOWN
- Signal logging: BEAR regime → SHORT only, BULL → LONG only, UNKNOWN → all
- Dashboard status bar shows regime with clickable modal (advice, aligned setups, execution guidance)

**Why Oracle was removed:**
- BTC Oracle: 9-33% WR across all timeframes — terrible for entry timing
- ETH Oracle: 7-21% WR — similarly broken
- Oracle as market gate was blocking valid Titan signals (BTC SELL blocked all LONGs)
- Regime detection (simple EMA50) provides better directional filtering

**Per-symbol risk overrides:** SYMBOL_OVERRIDES has been removed from `backend/app/strategies/titan.py`. Default ATR multipliers (SL=1.5x, TP adaptive 2.0x/3.0x) now apply uniformly to all symbols. Do not reference per-symbol overrides — they no longer exist in the codebase.

**Expanded backtest results (BTC/ETH/BNB, production settings):**
- BTC: 68 signals, 47.0% WR, +7.7R — workhorse
- ETH: 15 signals, 66.7% WR, +9.7R — best performer
- BNB: 12 signals, 40.0% WR, -0.7R — marginal
- SOL: **REMOVED** from watchlist (negative in all 7 configs tested)
- Production watchlist: BTCUSDT, ETHUSDT, BNBUSDT

**BTC-optimized Titan (0.46yr bear data):**
- Titan BTC-optimized (SL=1.75, TP=4.0): 26 trades, 38.5% WR, +0.264R EV
- HODL was -42.8%, trading at 5x gave +34.3% with 27% max DD

**Live signal performance (as of 2026-03-26):**
- 25 total live signals, 14W / 7L, **66.7% Win Rate** — strong edge confirmed in production
- BEAR regime active: all signals are SHORTs (SELL_LIMIT, Titan 60% confidence)
- BNB has consecutive losses (2x SL hits) — watch for regime bounces on this pair
- ETH SHORT open 4+ days without resolution — long-running signal, monitor closely

**Full results:** `docs/strategies/BACKTEST_RESULTS.md`
**Analysis scripts:** `backend/scripts/btc_*.py`, `backend/scripts/eth_*.py`, `backend/scripts/regime_detector.py`

**Why:** These findings drove the Oracle deprecation and regime detection system.
**How to apply:** Oracle is gone from UI — don't reference it as active. Titan + regime is the current system. Backtest before any parameter changes.

**Counter-regime signal tracking (2026-03-26):**
- Best Setups UI shows all signals (regime-aligned + counter) — purely for browsing
- Scanner job logs regime-aligned signals as `source='scanner'` (conviction ≥ 50) → eligible for paper trading
- Counter-regime signals logged as `source='counter'` (conviction ≥ 50) → tracked for observation only, never traded
- `execute_signals` job filters `source IN ('live', 'scanner')` — counter signals are safe from execution
- Signal Log UI has a new "Counter" tab to browse these setups and observe outcomes over time
- Purpose: accumulate performance data on counter-regime signals to evaluate whether they have edge

**Regime lag problem identified (2026-04-02):**
- Weekly EMA50 regime stayed BEAR while BTC pumped on 4H — all shorts stopped out (9/10 losses, -$688 in 10 trades)
- Root cause: weekly EMA50 is too slow to detect intra-week trend reversals
- Hard regime gate (`signal_log.py:244-248`) blocks all longs in BEAR, all shorts in BULL — no middle ground
- Titan's 4H EMA200 was showing BULLISH but weekly regime override forced shorts only
- **Planned fix (Option D): multi-timeframe confirmation** — require 4H EMA200 trend to agree with weekly regime before firing. If they disagree → no trades (sit on hands). Prevents trading during regime transitions.
- Also consider adding a consecutive-loss circuit breaker as a safety net
- **Why:** Lagging weekly regime + hard gate = catastrophic losses during trend reversals
- **How to apply:** Before implementing, backtest Option D against historical regime transitions. Use `/regime-check` skill to monitor for timeframe disagreement.
