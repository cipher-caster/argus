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
