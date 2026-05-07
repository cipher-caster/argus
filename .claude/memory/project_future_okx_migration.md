---
name: Future Plan - OKX Provider Migration Analysis
description: Planned work to analyze impact of switching live trading from Binance to OKX provider
type: project
---

## OKX Provider Migration Analysis (Future Phase)

**Status:** Planned (post-Phase C test expansion)

**Why:** OKX provider support exists for backtesting (9dc23e8, #2). Before switching live trading from Binance to OKX, need comprehensive analysis to ensure:
1. Position management works identically on OKX (order types, fills, cancellation)
2. Risk manager constraints stay within OKX account limits (margin, collateral)
3. Signal outcomes (TP/SL resolution) remain accurate with OKX candles/fills
4. Paper trading orchestrator handles OKX-specific order behavior

**Key Questions to Answer:**
- Do open positions resolve correctly on OKX vs Binance?  (same candle data, fill prices, slippage patterns?)
- Are risk gates (position sizing, correlation groups, drawdown limits) still effective on OKX?
- Does the backtest-to-live performance gap change on OKX? (fill rate, execution latency, fee structure)
- Which signals currently perform best on Binance but NOT on OKX? (provider-specific edge case?)
- What's the risk of switching mid-portfolio? (open positions on Binance, new signals on OKX)

**Implementation Tasks:**
1. **Analysis Script:** Backtest all signals on OKX historical data, compare WR/Rproft vs Binance
2. **Risk Assessment:** Document OKX order limits, margin rules, fee structure vs Binance
3. **Orchestrator Testing:** Paper trade with OKX provider for 1–2 weeks, compare fills/outcomes to Binance
4. **Migration Plan:** Define cutover strategy (keep Binance positions, route new signals to OKX? Or full switch?)
5. **Monitoring Hooks:** Real-time comparison metrics (fill rate, drawdown, signal latency)

**Success Criteria:**
- OKX backtest performance ≥95% of Binance WR on primary watchlist
- No new risk manager violations introduced on OKX
- Fill rate and execution latency within ±10% of Binance
- Zero cascading failures in position resolution or orchestrator

**Dependencies:**
- OKX provider fully integrated (✓ done)
- Phase C test expansion complete (signal-position joins, regime capture)
- Paper trading engine stable in production on Binance (80% fill rate achieved v0.9.2)

**Timeline:** Post-Phase C (estimated Q2 2026)

**How to apply:** Use this plan before proposing any provider switch. Reference backtest comparison results, orchestrator stability metrics, and risk assessment findings.
