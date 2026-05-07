---
name: Risk Config Rollback History
description: Production trading risk config history — 7% risk was tried and reverted to 3%. Don't re-propose without new evidence.
type: project
originSessionId: baf2c49a-e5f7-4c9f-bf4c-48d0bbf96298
---
On 2026-04-05 (commit 6ceffbb) `max_position_size_pct` was raised from 3% → 7% and the $200/7-day observation period was discontinued. It was later reverted to 3% (runtime Redis config change, no commit) — current live config as of 2026-04-17 is 3% risk, $1000 balance, 2× leverage, 15% drawdown, 200% exposure cap, min_conviction=50, SL=1.5× ATR, TP=2.0× ATR.

**Why:** The 7% sizing was reverted — likely produced uncomfortable drawdowns or volatility. User confirmed "we backrolled to the current config to tests" but did not remember specifics.

**How to apply:** Do NOT recommend raising position size back to 7% or above without new backtest/live evidence justifying it. The optimizer's "best experiment" (id=7: conviction=65, SL=1.0×, adaptive TP, macro guards) is a **separate** config that has `is_production: false` — it was never shipped, so recommending it is not a re-tread. Distinguish between "already tried and reverted" (7% risk) and "never shipped" (tight conviction experiment) when proposing config changes.
