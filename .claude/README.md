# Argus — Claude Code Configuration

This directory is the **portable bundle**. After cloning the repo and running the installer, your Claude Code picks up everything we've built: project memory, slash commands, subagents, hooks, settings, and (optionally) user-global rules.

## Bundle map

| Path | What it is | Loaded by Claude Code? |
|---|---|---|
| `commands/` | Slash commands (`/read`, `/trade`, `/portfolio`, `/optimize`, `/review`, `/backtest`, `/regime-check`) | Yes — auto. |
| `agents/` | Domain subagents (currently `code-reviewer.md` — opus reviewer with Argus-specific checklist) | Yes — auto. |
| `hooks/` | Shell scripts referenced from `settings.json` (e.g. `pre-commit-checks.sh`) | Yes — via settings. |
| `memory/` | Persistent project memory: user prefs, feedback rules, project state, references | **No** — needs the symlink installed once. |
| `global/` | Optional user-global rules (e.g. subagent model policy). Applies to ALL your projects, not just Argus. | **No** — opt-in via `--with-global`. |
| `settings.json` | Project Claude Code settings (model, permissions, env vars, hook registry) — committed. | Yes — auto. |
| `settings.local.json` | Per-machine overrides — gitignored. | Yes — auto. |
| `install.sh` | One-time installer that wires `memory/` (and optionally `global/`) into your `~/.claude` paths. | Run it. |

The repo-root `CLAUDE.md` is the project instructions file and is auto-loaded by Claude Code; it lives at the root so the framework finds it without configuration.

## First-time setup

```bash
# minimum: symlink project memory
bash .claude/install.sh

# also pull in user-global rules (subagent model policy)
bash .claude/install.sh --with-global

# only install the global rules, skip project memory
bash .claude/install.sh --global-only

# copy project memory instead of symlinking (private snapshot, no sync back)
bash .claude/install.sh --copy

# combine: copy memory AND install global
bash .claude/install.sh --copy --with-global
```

After setup, restart Claude Code in this repo. You should see the slash commands listed, and the project memory loaded.

## Why memory needs a separate step

Claude Code reads project memory from `~/.claude/projects/<hashed-absolute-repo-path>/memory/`. The hashed path depends on where you cloned, so the repo can't ship files there directly. The installer computes the hash and symlinks `.claude/memory/` into the right place — after that, memory edits flow through git like any other file.

## What's in `memory/`

- `MEMORY.md` — the index Claude reads on every session (keep it under ~150 lines)
- `user_*.md` — user role/preferences
- `feedback_*.md` — guidance learned from prior conversations (e.g. "always backtest before deploy", "OKX is default provider", "never override a closed experiment")
- `project_*.md` — project state, version, ongoing work, closed experiments
- `reference_*.md` — pointers to external docs/results

When Claude learns something durable, the relevant file is updated. Commit it so the next teammate (or your next machine) inherits the learning.

## What's in `commands/`

Argus-specific slash commands. Type `/` in Claude Code to see them. The most-used:

- `/read` — market or coin intelligence report from live APIs
- `/portfolio` — paper trading portfolio + P&L
- `/trade` — trading config + recent events *(model-invocation locked — only fires when you type the slash)*
- `/backtest` — run signal backtest on the watchlist
- `/optimize` — sweep params, analyze, apply *(model-invocation locked)*
- `/review` — full system review (pipeline health, docs, memory, plan)
- `/regime-check` — regime alignment diagnostic

## What's in `agents/`

Custom subagents Claude can delegate to. Currently:

- `code-reviewer.md` — opus reviewer with a domain-specific checklist (gate parity, closed-experiment guards, exception hierarchy, OKX assumption). Invoke with: *"Use the code-reviewer subagent to review the diff."*

## What's in `global/`

Optional rules that apply to **all** your Claude Code projects, not just Argus. Currently the subagent model policy (haiku/sonnet/opus by complexity). Installed only with `--with-global` or `--global-only` so collaborators can choose whether to adopt it.

## What's in `hooks/`

- `pre-commit-checks.sh` — runs `npx tsc --noEmit` on frontend changes and `pytest --collect-only` on backend changes before any `git commit`. Registered as a `PreToolUse` hook in `settings.json`.

## Updating the bundle

When you change anything under `.claude/` (or a memory file via the symlink), commit it like normal source. New collaborators get the latest after `git pull`. If `install.sh` itself changes, re-run it.

## Project-root CLAUDE.md

Lives at `../CLAUDE.md`, not in this directory — that's where Claude Code expects project instructions. It includes a Compact Instructions block so closed-experiment guards survive auto-compaction.
