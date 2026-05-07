---
name: Audit recommendations must not override closed experiments
description: When an audit recommends changing a parameter that has a closed experiment memory, surface the conflict before applying — never apply silently
type: feedback
---

When an audit (or any analytical pass) recommends changing a parameter that has a `project_*_experiment.md` or similar closed-experiment memory, STOP and surface the conflict to the user before applying the change. Never let a subagent apply it silently.

**Why:** On 2026-05-07, a backend audit recommended raising `min_conviction` from 56→60. The exact same change was already tried on 2026-04-17 and reverted on 2026-04-20 with documented WR data (75.7% over 70 trades at 56). The audit's reasoning was theoretical ("BUY_LIMIT is marginal class"); the closed experiment had empirical data. The Opus subagent applied the change anyway because the orchestrator hadn't checked the conflict before delegating. User caught it before commit.

**How to apply:**
- Before any change to a numeric param (conviction, risk %, expiry, ATR mult, etc.), grep `.claude/memory/project_*` for that param name.
- If a closed-experiment memory references that param with data, treat the audit recommendation as a *proposal* requiring backtest evidence — not a fix to apply.
- In the orchestrator turn (not in subagent prompts), state the conflict to the user: "audit says X, memory says Y closed with data Z, what's the call?"
- Only when the user agrees, then delegate the change.

**Hard rule:** theoretical reasoning never overrides empirical results captured in a closed-experiment memory. Backtest evidence does.
