---
name: Subagent model policy — pick by task complexity
description: For Argus orchestration, pick agent model by task complexity (haiku/sonnet/opus). The global rule lives in ~/.claude/CLAUDE.md; this file is the project-local reminder.
type: feedback
originSessionId: 4a4dab53-395e-4e1b-ac1d-876426772660
---
For mid-to-complex Argus tasks, orchestrate by spawning subagents via the Agent tool — don't do everything inline. Pick the model by task complexity:

- **haiku** — trivial single-shot lookups (one grep, one file read).
- **sonnet** — mid-complexity research, focused implementation, audits with a clear scope, checklist-driven review. Most common choice.
- **opus** — open-ended design, hard debugging, adversarial review of risky changes (e.g. trading-engine modifications).

**Why:** User updated the prior "always Sonnet" rule on 2026-05-08. Reason: cost-vs-capability fit — haiku is fine for noise, opus earned for risk, sonnet is the workhorse default.

**How to apply:**
- Multi-step / multi-file / exploration+implementation tasks → delegate, don't do inline.
- Run independent agents in parallel (single message with multiple Agent blocks).
- Use the `code-reviewer` subagent (`.claude/agents/code-reviewer.md`, opus) for any change to trading, signal-log, or backtest_engine code before commit.
- Trivial reactive tasks stay inline — don't over-delegate.

The full policy lives in `~/.claude/CLAUDE.md` and applies across all projects.
