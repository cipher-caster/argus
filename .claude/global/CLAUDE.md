# Global preferences (apply across all projects)

## Subagent model policy

When spawning subagents via the `Agent` tool, pick the model by task complexity — do not default to one fixed model.

- **haiku** — trivial, single-shot lookups: one grep, one file read, one well-defined transformation. No exploration, no judgment calls.
- **sonnet** — mid-complexity work: multi-file research, focused implementation, audits with a clear scope, code review with a checklist. This is the most common choice.
- **opus** — hard problems: open-ended design, debugging across unfamiliar surfaces, multi-step planning where the wrong first step compounds, adversarial review of risky changes.

Pick once per agent at spawn time; don't second-guess mid-stream. When in doubt, prefer sonnet — it's the cheapest model that handles judgment well. Reserve opus for tasks where the cost of a wrong answer outweighs the cost of the bigger model.

When parallelizing, you may mix models — e.g. three sonnet researchers feeding one opus synthesizer.

## Orchestration default

For mid-to-complex tasks, prefer delegating to subagents over working inline. Inline burns the main context window; subagents protect it and let you run things in parallel.

Reactive single-step tasks (one edit, one read, one grep) stay inline.

## Orchestration loop

The portable dev backbone (installed via `install.sh --with-core`) gives you four generic agents and three drivers. For any non-trivial change, act as an orchestrator and run:

```
explore  ->  plan  ->  implement  ->  review  ->  verify
 Explore     Plan     implementer  diff-reviewer test-runner
(built-in) (built-in)               (+ project reviewer, if any)
```

- **explore** — built-in `Explore` agents (read-only, parallel) to map code and find reusable patterns.
- **plan** — built-in `Plan` agent (or inline for small work); reuse existing utilities over new code.
- **implement** — `implementer` makes the bounded change and runs the directly-relevant tests.
- **review** — `diff-reviewer` (generic) plus any project-specific reviewer (e.g. `code-reviewer`).
- **verify** — `test-runner` runs the project's tests/build/typecheck/lint.

Loop back to implement on any `NEEDS CHANGES` / `FAIL`. Subagents do not dispatch each other — orchestration runs from the main agent / driver. The agents discover each project's commands from that project's `CLAUDE.md` "Commands" section, so give every project one.

Entry points:

| You want… | Use |
|---|---|
| Run a change end-to-end, no approval gate | `/dev <task>` |
| Same loop but approve the plan before edits | native **plan mode** |
| Fix a bug (root-cause → minimal fix → regression test) | `/fix <bug>` |
| Think/investigate with a hard guarantee of no edits | `/discuss <topic>` |
| One small reactive edit/read/grep | inline — don't orchestrate |

## Engineering principles

Apply these while writing and reviewing code (heuristics, not dogma — the parenthetical tensions
matter as much as the rules):

- **KISS** — simplest thing that works; optimize for the next reader, avoid cleverness.
- **DRY** — don't duplicate logic — *but* don't over-abstract; a little duplication beats the wrong
  abstraction (rule of three before extracting).
- **YAGNI** — build only what the task needs now; no speculative generality.
- **SRP / separation of concerns** — one reason to change per unit; keep layers distinct.
- **Explicit over implicit** — obvious data flow and names over magic/hidden side effects.
- **Fail fast** — validate at boundaries, raise early with clear errors (use the project's exception
  hierarchy where one exists).
- **Least astonishment** — match the surrounding code's patterns, naming, and idioms.
- **Small, focused changes; boy-scout rule** — minimal diff; leave touched code a little cleaner,
  without scope-creeping into unrelated refactors.
