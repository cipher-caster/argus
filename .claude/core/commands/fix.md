---
description: Diagnose and fix a bug — root-cause, minimal fix, regression test, verify, review. Orchestrates debugger + implementer + test-runner.
disable-model-invocation: true
---

# /fix — bug loop

Fix the bug described in `$ARGUMENTS`. You are the **orchestrator**; dispatch subagents and
integrate their results. The goal is a *minimal* fix at the *root cause*, with a regression test so
the bug can't return.

## Loop

1. **Diagnose.** Dispatch the `debugger` agent. It reproduces the bug, traces it to the root cause,
   and returns a precise fix spec (file:line + what to change + where the regression test belongs).
   If it can't reproduce, surface that to the user before guessing.
2. **Fix.** Dispatch the `implementer` with the debugger's fix spec as a bounded spec. Require it to
   add (or update) the regression test the debugger identified.
3. **Verify.** Dispatch `test-runner` to confirm the regression test now passes and nothing else
   broke (tests / build / typecheck, discovered from `CLAUDE.md`).
4. **Review.** Dispatch `diff-reviewer` (and any project-specific reviewer) on the fix diff.
5. **Iterate.** On `FAIL` or `NEEDS CHANGES`, feed the findings back to the `implementer` and repeat
   from step 3 until green and approved, or until blocked — then stop and report.

## Report

End with: root cause (one line), the fix (files), the regression test added, verify result, and
review verdict. Do not commit or push unless the user asks.
