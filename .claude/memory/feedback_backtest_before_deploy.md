---
name: Always backtest strategy changes before deploying
description: User wants data-driven validation of strategy changes, not just theory — run backtest script to measure impact
type: feedback
---

Always backtest strategy changes before deploying to production.

**Why:** User values empirical evidence over theoretical reasoning. During Phase 11, running 4 incremental experiments revealed that the "obvious" fix (blocking SLEEPING) actually hurt WR alone, while the adaptive TP fix was the real game-changer — something theory wouldn't have predicted.

**How to apply:** When modifying Oracle, Titan, market gate, or signal logic:
1. Run `docker compose exec backend python scripts/run_signal_backtest.py --dry-run` to see baseline
2. Add experiment flags for the change
3. Compare metrics (WR, total profit in R, REVIEW rate) before applying to production
4. User wants to see the numbers, not just the reasoning
