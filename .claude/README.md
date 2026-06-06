# Argus — Claude Code Configuration

This directory is the project's [Claude Code](https://claude.com/claude-code) bundle. When you open the repo in Claude Code it auto-loads the slash commands, subagents, settings, and the orchestration backbone described below.

## Bundle map

| Path | What it is | Loaded by Claude Code? |
|---|---|---|
| `commands/` | Argus-specific slash commands (`/read`, `/trade`, `/portfolio`, `/optimize`, `/review`, `/backtest`, `/regime-check`) | Yes — auto (project scope). |
| `agents/` | Argus-specific subagents (`code-reviewer.md` — reviewer with an Argus checklist) | Yes — auto (project scope). |
| `core/` | Project-agnostic dev orchestration backbone — generic dev agents + drivers (`/dev`, `/fix`, `/discuss`). | Yes — auto (project scope). |
| `hooks/` | Shell scripts referenced from `settings.json` (e.g. `pre-commit-checks.sh`). | Yes — via settings. |
| `settings.json` | Project Claude Code settings (model, permissions, env vars, hook registry). | Yes — auto. |

The repo-root `CLAUDE.md` is the project instructions file and is auto-loaded by Claude Code; it lives at the root so the framework finds it without configuration.

## What's in `commands/`

Argus-specific slash commands. Type `/` in Claude Code to see them. The most-used:

- `/read` — market or coin intelligence report from live APIs
- `/portfolio` — paper trading portfolio + P&L
- `/trade` — trading config + recent events *(model-invocation locked — only fires when you type the slash)*
- `/backtest` — run signal backtest on the watchlist
- `/optimize` — sweep params, analyze, apply *(model-invocation locked)*
- `/review` — full system review (pipeline health, docs, plan)
- `/regime-check` — regime alignment diagnostic

These call the live Argus APIs, so the backend must be running (`docker-compose up -d`).

## What's in `agents/`

Custom subagents Claude can delegate to. Currently:

- `code-reviewer.md` — reviewer with a domain-specific checklist (gate parity, exception hierarchy, OKX assumption). Invoke with: *"Use the code-reviewer subagent to review the diff."*

## What's in `core/` (the orchestration backbone)

`core/` is a **project-agnostic development orchestration layer** — reusable dev agents and drivers.

**Generic agents** (`core/agents/`), tiered by model:

- `implementer` (sonnet) — bounded code-writer: takes a spec, edits the named files, runs the relevant tests.
- `test-runner` (sonnet) — runs tests/build/typecheck/lint, returns a distilled pass/fail. Read-only.
- `diff-reviewer` (sonnet) — generic correctness/reuse/regression review. Named distinctly from the Argus `code-reviewer` so it never shadows it — run *both* (generic + domain). Read-only.
- `debugger` (opus) — root-cause investigator; produces a minimal fix spec for the implementer. Read-only.

**Drivers** (`core/commands/`), all manual-invocation only:

- `/dev <task>` — full loop: explore → plan → implement → review → verify, autonomous (no approval gate). Use native plan mode instead when you want to approve the plan before edits.
- `/fix <bug>` — debug → minimal fix + regression test → verify → review.
- `/discuss <topic>` — read-only thinking partner (cannot edit or spawn editing subagents for that turn).

The orchestration policy lives in `core/ORCHESTRATION.md`.

## What's in `hooks/`

- `pre-commit-checks.sh` — runs `npx tsc --noEmit` on frontend changes and `pytest --collect-only` on backend changes before any `git commit`. Registered as a `PreToolUse` hook in `settings.json`.
