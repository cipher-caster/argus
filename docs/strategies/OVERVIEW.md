# Argus Trading Strategies

Argus uses **Titan** as its primary trading strategy, filtered by a **BTC weekly regime detection** system. Oracle (Prophet v9.0) is preserved in the backend but **deprecated from all UI** as of v0.9.0 (negative EV on BTC/ETH — see `docs/strategies/BACKTEST_RESULTS.md`).

---

## Regime Detection — Market Direction Filter

**API**: `GET /api/strategy/regime`

BTC weekly EMA50 determines the macro direction:
- **BULL** (BTC > weekly EMA50): favor LONG setups only
- **BEAR** (BTC < weekly EMA50): favor SHORT setups only
- **UNKNOWN**: no direction filter

Used by: signal logging, best-setups endpoint, dashboard status bar, CoinAnalysisModal.

---

## Primary Strategy: Titan — Unified Trend + Momentum

**Class**: `TitanStrategy` in `backend/app/strategies/titan.py`
**API**: `GET /api/strategy/titan/{symbol}`

A hybrid strategy combining trend structure with momentum confirmation.

- **Signals**: `BUY`, `SELL`, `BUY_LIMIT`, `SELL_LIMIT`, `WAIT_OB`, `WAIT_OS`
- **Confidence**: 0–100 score
- **Best for**: 4H entries with momentum confirmation
- **Per-symbol overrides**: BTC uses wider stops/targets (SL=1.75x ATR, TP=4.0x ATR) via `SYMBOL_OVERRIDES` dict. See `docs/strategies/BACKTEST_RESULTS.md` for analysis.

See `docs/analytics/TITAN_STRATEGY.md` for full signal logic.

---

## Earnest Brain (Voting System)

Used by Oracle. Calculates the -4 to +4 Earnest Score:

| Voter | Bullish (+1) | Bearish (-1) | Neutral (0) |
|---|---|---|---|
| **RSI** | 50 < RSI < 70 | 30 < RSI < 50 | Extremes (≥70 or ≤30) |
| **Bollinger** | BB pos > 0.1 | BB pos < -0.1 | Near midband |
| **ADX** | ADX > 20 & price > EMA200 | ADX > 20 & price < EMA200 | ADX ≤ 20 |
| **EMA** | Price > EMA200 | Price < EMA200 | — |

---

## Oracle (Prophet v9.0) — Deprecated from UI

**Class**: `OracleStrategy` in `backend/app/strategies/oracle.py`
**API**: `GET /api/strategy/oracle/{symbol}` (backend preserved, not used in UI)

Combines an "Earnest Brain" micro-analysis with a "Prophet" macro-context filter. **Deprecated** because backtesting showed 9-33% WR on BTC and 7-21% on ETH — fundamentally broken for trending assets.

See `docs/DEAD_CODE.md` for the full list of dead Oracle UI components.

---

## Live Backtesting & Performance

Oracle's `_run_backtest()` simulates trades on historical candles:

- **Trade targets**: TP = ATR × 3.0, SL = ATR × 1.5 (2:1 reward-to-risk)
- **Break-even win rate**: 33.3% (at 2:1 RR)
- **Metrics returned**: `win_rate`, `total_trades`, `net_profit`, last 5 trades detail

Win rate thresholds used in Best Setups cards:
- ≥ 50% → green (solidly profitable)
- 33–49% → yellow (marginal but above break-even)
- < 33% → red (below break-even)
- `null` when total_trades < 10 (insufficient sample)

---

## Eliz + Mayne MTF Confluence

Best Setups cards show Titan signal confirmation across 4 timeframes, based on the Eliz (@eliz883) + Trader Mayne (@Tradermayne) framework:

- **Eliz lane**: 4H (entry trigger) + 1D (swing structure)
- **Mayne lane**: 12H (higher-TF bias) + 1W (macro/weekly direction)

All four confirmed = full confluence swing trade. Partial confirmation = lower-timeframe or entry-only setup.
