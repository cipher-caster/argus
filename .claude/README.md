# Argus — Claude Code Configuration

This directory ships everything Claude Code needs to work effectively in this repo:

| Path | What it is | Auto-loaded? |
|---|---|---|
| `commands/` | Project slash commands (`/read`, `/trade`, `/portfolio`, `/optimize`, `/review`, `/backtest`, etc.) | Yes — Claude Code picks them up from `.claude/commands/` automatically. |
| `hooks/` | Git pre-commit and other hook scripts | Yes — registered via `settings.json`. |
| `memory/` | Persistent project memory (user prefs, project state, feedback rules, references) | **No** — needs one-time install. See below. |
| `settings.json` | Project-level Claude Code settings (committed) | Yes. |
| `settings.local.json` | Per-machine overrides (gitignored) | Yes. |
| `install.sh` | One-time installer for the memory dir | Run it. |

## First-time setup

After cloning, run:

```bash
bash .claude/install.sh
```

This symlinks `.claude/memory/` to `~/.claude/projects/<hashed-repo-path>/memory/`, which is where Claude Code looks for project memory. With the symlink, edits to memory files are tracked in git — pull from anyone's machine and you stay in sync.

If you'd rather not symlink (e.g. you want a private snapshot):

```bash
bash .claude/install.sh --copy
```

## Why memory needs a separate step

Claude Code reads project memory from a user-level path derived from the repo's absolute location on disk. That path differs per machine and per user, so the repo can't ship files there directly. The install script does the path math for you.

## What's in `memory/`

- `MEMORY.md` — the index Claude reads on every session
- `user_*.md` — user role/preferences
- `feedback_*.md` — guidance learned from prior conversations (e.g. "always backtest before deploy", "OKX is default provider")
- `project_*.md` — project state, version, ongoing work, closed experiments
- `reference_*.md` — pointers to external docs/results

When you finish a session and Claude has learned something new, the relevant `*.md` file is updated. Commit the change so the next teammate (or your next machine) inherits the learning.

## What's in `commands/`

Argus-specific slash commands. Type `/` in Claude Code to see them. The most-used:

- `/read` — market or coin intelligence report from live APIs
- `/portfolio` — paper trading portfolio + P&L
- `/trade` — trading config + recent events
- `/backtest` — run signal backtest on the watchlist
- `/optimize` — sweep params, analyze, apply
- `/review` — full system review (pipeline health, docs, memory, plan)
- `/regime-check` — regime alignment diagnostic

## CLAUDE.md

Lives at the repo root, not in `.claude/`. Auto-loaded by Claude Code as project instructions.
