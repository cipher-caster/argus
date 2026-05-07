---
name: v2 methodology review checkpoint
description: Scheduled ~2026-06-01 review to compare v1 vs v2 signal performance after the P0 trading correctness fixes
type: project
originSessionId: 1f5b6b5a-ea47-4ba9-87d4-8690f44ca852
---
Review scheduled for ~2026-06-01 after ~6 weeks of v2 signal accumulation.

**Why:** P0 fixes (MSS lookahead, forming candle, methodology versioning) were applied 2026-04-19. All pre-fix data is tagged v1. Need real v2 data to judge whether the bias materially inflated reported edge.

**Two questions to answer:**
1. v1 vs v2 win rate delta per coin — did the MSS lookahead/forming candle bias matter (>3% gap = significant)
2. Sharpe/Calmar telling a different story than win rate — watchlist rebalancing needed? (ATOMUSDT swap + ADX gate evaluation)

**How to apply:** Around 2026-06-01 run `/review` or check Analytics with `include_legacy=true` to compare v1 vs v2 side-by-side. Use Sharpe and Calmar as primary metrics, not just win rate. Conviction threshold is settled at 56 — don't revisit unless v2 data shows a clear structural break.
