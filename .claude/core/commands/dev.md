---
description: Drive a feature or change end-to-end — explore, plan, implement, review, verify. Autonomous (no approval gate). Orchestrates the generic dev agents.
disable-model-invocation: true
---

# /dev — feature / change loop

Run the full development loop for the task in `$ARGUMENTS`. You are the **orchestrator**: you
decompose the work and dispatch subagents; the subagents do not dispatch each other. Serialize
dependent steps, parallelize independent ones.

> **Relationship to plan mode:** `/dev` is the *autonomous* path — it runs end-to-end without an
> approval gate. Native plan mode runs the *same loop but stops for plan approval before edits*.
> Do **not** call ExitPlanMode from `/dev`; just proceed. (If the user wanted an approval gate they'd
> be in plan mode, not running `/dev`.)

## Loop

1. **Explore.** Launch built-in `Explore` agent(s) in parallel (one per distinct area) to map the
   relevant code, existing patterns, and reusable helpers. Read-only; you only need the conclusions.
2. **Plan.** Synthesize a short implementation plan from the exploration: the files to touch, the
   approach, and acceptance criteria. For non-trivial work, use the built-in `Plan` agent; for small
   changes, plan inline. Reuse existing utilities over writing new code.
3. **Implement.** Dispatch the `implementer` agent with a **bounded spec** (named files + acceptance
   criteria). For independent sub-changes, dispatch implementers in parallel; for dependent ones,
   serialize and feed each result into the next.
4. **Review.** Dispatch `diff-reviewer` on the resulting diff. If a project-specific reviewer exists
   (e.g. `code-reviewer`), dispatch it too and treat its verdict as authoritative for that domain.
5. **Verify.** Dispatch `test-runner` to run the project's tests / build / typecheck / lint
   (discovered from `CLAUDE.md`).
6. **Iterate.** If review returns `NEEDS CHANGES` or verify returns `FAIL`, re-dispatch `implementer`
   with the specific findings as the new spec. Repeat from step 4 until review is `APPROVED` and
   verify is `PASS`, or until you're blocked — then stop and report what's blocking.

## Report

End with: what changed (files), review verdict, verify result, and anything left for the user
(decisions, follow-ups, or a blocked step). Do not commit or push unless the user asks.
