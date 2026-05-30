---
name: project_orchestration_backbone
description: Portable agent-orchestration backbone (.claude/core/) — generic dev agents + /dev /fix /discuss drivers + Obsidian context backup
metadata:
  type: project
---

A reusable, project-agnostic development orchestration layer lives in `.claude/core/` (canonical
source) and installs user-global via `bash .claude/install.sh --with-core` (per-file symlinks into
`~/.claude/agents` and `~/.claude/commands`, so it's available in every project). Built 2026-05-30.

**Generic agents** (`core/agents/`): `implementer` (sonnet), `test-runner` (sonnet, read-only),
`diff-reviewer` (sonnet, read-only — named distinctly so it never shadows the Argus
[[project_strategy_findings]] `code-reviewer`; run both), `debugger` (opus, read-only). They discover
each project's test/build commands from that project's `CLAUDE.md` "Commands" section.

**Drivers** (`core/commands/`, all `disable-model-invocation: true`): `/dev` (explore→plan→implement
→review→verify, autonomous — does NOT call ExitPlanMode; use plan mode when you want an approval
gate), `/fix` (debug→minimal fix+regression test→verify→review), `/discuss` (read-only thinking
partner; the guard is `disallowed-tools: Edit, Write, NotebookEdit, Agent`, which REMOVES those from
the pool for the turn — note `allowed-tools` only pre-approves and does NOT restrict, per the skills
spec; the disallowed-tools restriction is per-turn and clears on the next user message). Loop policy
is mirrored into the global `~/.claude/CLAUDE.md`.

**Obsidian context backup:** `core/hooks/backup-context.sh` mirrors the bundle into
`~/Documents/obsidian/claude_context/<repo>/` (+ `_global/` for `~/.claude` agents/commands/skills/
CLAUDE.md) on `SessionStart` and `UserPromptExpansion` (and `PreToolUse:Skill`), registered in
`settings.json`. Latest-mirror via `rsync -aL --delete` + append-only `_backup-log.md`, debounced
~30s, secrets excluded (`*.local.json`, `.credentials*`, chat logs, `.bak`, `worktrees/`), no-ops
if the vault is missing. This Obsidian use is **config backup only** — it does NOT override
[[feedback_docs_not_obsidian]] (findings/reports still go in `docs/`).
