---
name: Min Conviction Experiment — Closed
description: min_conviction experiment concluded 2026-04-20; reset to 56 (data-driven floor)
type: project
originSessionId: 6c6f612a-2e69-416d-8f8b-a2b5bdbdda71
---
Conviction experiment opened 2026-04-17 (raised 50→60), closed 2026-04-20.

**Result:** min_conviction=60 was too high. It silently killed the entire standard-trend signal class.

Titan has only 6 discrete confidence values: 0, 60, 80, 90, 95, 100. Standard trend continuation (clean trend, no RSI extreme, no SMC event) always produces confidence=60 → conviction=56. Zero signals fired in the 3 days at gate=60.

**Final setting: min_conviction=56** — the data floor, not a round number.

**Why 56:**
- Live signals at conv=56: 75.7% WR over 70 resolved trades
- Scanner signals at conv=56: 64.8% WR over 125 signals
- Setting gate above 56 = disabling standard-trend path entirely

**How to apply:** Do not raise min_conviction above 56 without understanding that anything >56 blocks Titan's most common signal type. If raising, target 68+ (the next natural Titan level: confidence=80 → conviction=68) — not an intermediate value like 60 or 65.

**Repeat offense 2026-05-07:** A backend audit recommended 56→60 again, citing the same BUY_LIMIT-class reasoning as the original 2026-04-17 experiment. An Opus subagent applied it. User caught and reverted before commit. Lesson reinforced: theoretical reasoning ("class X is marginal") is not data. The 56 floor is set on 75.7% WR over 70 trades — overriding it requires backtest evidence at the new floor, not logic.
