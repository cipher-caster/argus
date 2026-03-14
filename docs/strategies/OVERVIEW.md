# Argus Trading Strategies

Argus includes two professional-grade trading strategies ported from Pine Script (TradingView) to Python, allowing for real-time market scanning and live backtesting.

---

## Strategy 1: Oracle (Prophet v9.0) — Swing Trend Following

**Class**: `OracleStrategy` in `backend/app/strategies/oracle.py`
**API**: `GET /api/strategy/oracle/{symbol}`

The core scoring engine. Combines an "Earnest Brain" micro-analysis with a "Prophet" macro-context filter.

- **Earnest Brain**: 4-voter confluence system (RSI, Bollinger, ADX, EMA) → score -4 to +4
- **Macro Filter**: Daily Ichimoku Cloud + EMA200 + OBV trend check → BULLISH / NEUTRAL / BEARISH
- **Signal synthesis**: `STRONG_BUY`, `BUY`, `STRONG_SELL`, `SELL`, `NEUTRAL`
- **Best for**: 1H/4H swing entries with daily trend alignment

See `docs/analytics/ORACLE_SCREENER.md` for full voter logic.

---

## Strategy 2: Titan — Unified Trend + Momentum

**Class**: `TitanStrategy` in `backend/app/strategies/titan.py`
**API**: `GET /api/strategy/titan/{symbol}`

A hybrid strategy combining trend structure with momentum confirmation.

- **Signals**: `BUY`, `SELL`, `BUY_LIMIT`, `SELL_LIMIT`, `WAIT_OB`, `WAIT_OS`
- **Confidence**: 0–100 score
- **Best for**: 4H entries with momentum confirmation

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

## Live Backtesting & Performance

Both strategies expose backtest data. Oracle's `_run_backtest()` simulates trades on historical candles:

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
