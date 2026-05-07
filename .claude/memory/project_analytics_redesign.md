---
name: Analytics Page — Current State & Future Redesign
description: Analytics is now 2 tabs (Best Setups, Signal Log); Backtest Performance tab removed when WinRateTrend was also removed
type: project
originSessionId: e8dc91a7-8713-485f-bd3f-8e7acb71133b
---
**Current state (v1.1.4):**
Analytics page has 2 tabs:
1. **Best Setups** — Titan-only signals, all signals with trend/counter badges
2. **Signal Log** — Historical signals with resolution dates, 4 sources (Live/Scanner/Backtest/Counter)

Removed tabs: Backtest Performance (removed earlier), Win Rate Trend (built in v1.1.0, removed in commit 70074ed, 2026-04-17).

Removed components: OracleScreener, TitanRadar, TitanSignalsPanel, Contrarian Radar.

**Data model gaps (known, logged in CHANGELOG):**
- Signal log captures resolution-time context: `regime_at_resolution`, `btc_price_at_resolution`, `time_to_resolution_ms`
- Rejected signals persisted with `rejection_reason`
- Still missing: signal→position join (can't correlate signal WIN to actual PnL)

**Future redesign (not started):**
- New views: Win rate by strategy/coin/condition, PnL curve, risk gate audit, rejection analysis
- Two audiences: Claude (AI trader feedback loop) + User (performance visibility)

**Why:** Analytics should directly support profitability, not just display interesting data.
**How to apply:** Current 2-tab layout is stable. Don't add tabs without user request. Don't re-implement WinRateTrend — see project_phase19_plan.md.
