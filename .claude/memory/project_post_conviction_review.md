---
name: Post-Conviction Review — Completed 2026-04-20
description: All deferred signal-behavior items resolved on 2026-04-20
type: project
originSessionId: 6c6f612a-2e69-416d-8f8b-a2b5bdbdda71
---
All four deferred items resolved on 2026-04-20 (not waiting for 2026-05-01).

**Resolved:**

1. **block_btc_sell** — DELETED. Unwired stub removed from all layers (schema, job defaults, route defaults, tests, frontend type, UI toggle). No behavior existed; dead code surface eliminated.

2. **ADX gate on SHORT signals** — DEFERRED to 2026-06-01 v2 review. Insufficient v2 data to evaluate (only 6 v2 signals exist as of 2026-04-20).

3. **APTUSDT removed from watchlist** — 39.2% WR over 125 signals. Removed from all config layers and live Redis.

4. **ATOMUSDT liquidity review** — DEFERRED to 2026-06-01 v2 review. WR is neutral (49.2%) but needs v2 methodology data before deciding swap.

**How to apply:** Next batch review is 2026-06-01 for v2 methodology comparison. Remaining items: ATOMUSDT swap (SUI/AVAX/INJ candidates), ADX gate evaluation.
