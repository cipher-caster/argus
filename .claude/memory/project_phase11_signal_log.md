---
name: Signal Log system — sources, regime filtering, paper trading gate
description: Distinction between live/scanner/counter signal sources, what gets traded vs. scouted, and how paper trading connects
type: project
---

Signal log table (`signal_log`) has three `source` values with different scopes and purposes.

## Source Comparison

| Source | Job | Universe | Schedule | Traded? |
|--------|-----|----------|----------|---------|
| `live` | `log_watchlist_setups` | Watchlist only | 4H candle closes (6x/day) | ✅ Yes |
| `scanner` | `log_best_setups` | Top 100 by volume (all logged) | Every 5 min | ✅ Watchlist coins only |
| `counter` | `log_contrarian_signals` | Top 50 by volume | Every 10 min | ❌ Observation only |

## `live` — Signal Log Live Tab
- Runs Titan directly on each watchlist coin at 4H candle close.
- Most deliberate: based on completed candle data, not a cache snapshot.
- Regime-filtered (BTC weekly EMA50): BULL→LONG, BEAR→SHORT, UNKNOWN→all.
- Conviction threshold: configurable (default 55).

## `scanner` — Signal Log Scanner Tab
- Reads `best-setups` Redis cache (pre-warmed every 5 min by `sync_analytics_cache`).
- Logs signals from **all top-100 coins** — non-watchlist coins appear in Signal Log for scouting.
- **Trading gate in `execute_signals`**: filters to watchlist-only before sending to orchestrator. Non-watchlist scanner signals are tracked for outcome learning but never traded.
- Conviction threshold: configurable (default 50).

## Paper Trading
- `execute_signals` (every 10 min) picks up OPEN signals from `live` + `scanner` with no existing position.
- Watchlist filter applied — only watchlist coins passed to `TradeOrchestrator`.
- Risk gates: drawdown circuit breaker → max concurrent positions → correlated-pair limit → conviction gate → position sizing.
- Position lifecycle: `PENDING → OPEN → CLOSED / EXPIRED / CANCELLED`.
- Current config: 7% risk per trade, 2x leverage, 200% max exposure, 12% drawdown stop, 16h expiry.

**Key distinction**: Scanner logs broadly (scouting top 100), live trades precisely (watchlist only). Paper trading is the execution layer — acts only on watchlist-approved signals regardless of source.

**Why:** Signal log tracks all signals for learning/outcome resolution. Paper trading is intentionally scoped to backtested watchlist coins only.
**How to apply:** When reviewing open positions, they will only be watchlist coins. Scanner tab in Signal Log shows broader scouting data including non-watchlist coins.
