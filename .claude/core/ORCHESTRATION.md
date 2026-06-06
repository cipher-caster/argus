# Orchestration loop (portable backbone)

This is the project-agnostic development backbone — generic dev agents and drivers that layer
under any project-specific agents/commands. It lives in this repo at `.claude/core/`.

## The default loop

For any non-trivial change, work as an **orchestrator**: keep the main context for planning and
integration, and push the heavy lifting into subagents that each return only a summary.

```
explore  ->  plan  ->  implement  ->  review  ->  verify
   |          |            |            |           |
 Explore     Plan      implementer  diff-reviewer test-runner
(built-in) (built-in)                (+project reviewer)
```

- **explore** — built-in `Explore` agents (read-only, parallel) map the code and find reusable
  patterns. Use multiple only when the scope spans several areas.
- **plan** — built-in `Plan` agent (or inline for small work) decides the approach and acceptance
  criteria. Reuse existing utilities over new code.
- **implement** — `implementer` makes the bounded change and runs the directly-relevant tests.
- **review** — `diff-reviewer` (generic) plus any project-specific reviewer (e.g. `code-reviewer`).
- **verify** — `test-runner` runs the project's tests/build/typecheck/lint.

Loop back to implement on any `NEEDS CHANGES` / `FAIL`. Subagents do **not** dispatch each other —
orchestration runs from the main agent / driver.

## When to reach for which entry point

| You want… | Use |
|---|---|
| Run a change end-to-end, no approval gate | `/dev <task>` |
| Same loop but approve the plan before edits | native **plan mode** |
| Fix a bug (root-cause → minimal fix → regression test) | `/fix <bug>` |
| Think/investigate with a hard guarantee of no edits | `/discuss <topic>` |
| One small reactive edit/read/grep | just do it inline — don't orchestrate |

## Engineering principles

Apply these while writing and reviewing code. State them once here; agents and inline work follow
them. They are heuristics to be applied with judgment — the parenthetical tensions matter as much as
the rules.

- **KISS** — the simplest thing that works. Avoid cleverness; optimize for the next reader.
- **DRY** — don't duplicate logic — *but* don't over-abstract. A little duplication is cheaper than
  the wrong abstraction; prefer the rule of three before extracting.
- **YAGNI** — build only what the task needs now. No speculative generality, no unused hooks.
- **SRP / separation of concerns** — one reason to change per unit; keep layers distinct.
- **Explicit over implicit** — obvious data flow and clear names over magic and hidden side effects.
- **Fail fast** — validate at boundaries and raise early with clear errors (use the project's
  exception hierarchy where one exists).
- **Least astonishment** — match the surrounding code's patterns, naming, and idioms.
- **Small, focused changes; boy-scout rule** — minimal diff for the goal; leave touched code a little
  cleaner than you found it, without scope-creeping into unrelated refactors.

## Model tiering

Pick the agent's model by task complexity (see the model policy in the global CLAUDE.md): `haiku`
for trivial single-shot work, `sonnet` for most implementation/review/test work, `opus` for hard
open-ended debugging and design. The bundled agents default to `sonnet`, except `debugger` (`opus`).

## Portability

The agents discover each project's commands from that project's `CLAUDE.md` "Commands" section
rather than hardcoding them. To get the full benefit in a new project, give it a `CLAUDE.md` with a
Commands section describing how to run tests, build, and typecheck.
