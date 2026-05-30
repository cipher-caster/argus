#!/usr/bin/env bash
# Backup the Claude context bundle into the user's Obsidian vault.
#
# Part of the portable core backbone (.claude/core/). Registered in settings.json as a hook on
# SessionStart (once per session) and UserPromptExpansion (when a /command is typed), so skills,
# memory, agents, commands and the global backbone are mirrored automatically.
#
# Design:
#   - Latest-mirror (rsync --delete), NOT timestamped snapshots — no folder explosion.
#   - Mirrors this repo's .claude bundle AND the user-global backbone (~/.claude/agents,commands,
#     skills,CLAUDE.md). Secrets are excluded by the denylist below.
#   - Follows symlinks (-L) so the symlinked global agents/commands are backed up as real content.
#   - Debounced (~30s) so rapid successive commands don't thrash the vault.
#   - No-ops gracefully (exit 0) if the Obsidian vault parent doesn't exist — never errors a turn.
#
# Usage:  backup-context.sh [trigger-label]    e.g. backup-context.sh startup
# Hooks pass a JSON event on stdin; we don't require it, but enrich the label from it if jq exists.

set -uo pipefail

TRIGGER="${1:-manual}"
VAULT_PARENT="$HOME/Documents/obsidian"
VAULT="$VAULT_PARENT/claude_context"
DEBOUNCE_SECONDS=30

# Enrich the trigger label from the hook's stdin JSON when possible (command name / session source).
if [[ ! -t 0 ]] && command -v jq >/dev/null 2>&1; then
  payload="$(cat 2>/dev/null || true)"
  if [[ -n "$payload" ]]; then
    cmd="$(printf '%s' "$payload" | jq -r '.command_name // empty' 2>/dev/null || true)"
    src="$(printf '%s' "$payload" | jq -r '.source // empty' 2>/dev/null || true)"
    [[ -n "$cmd" ]] && TRIGGER="/$cmd"
    [[ -z "$cmd" && -n "$src" ]] && TRIGGER="$src"
  fi
fi

# The vault must already exist (we create claude_context/ inside it, but not the vault itself).
if [[ ! -d "$VAULT_PARENT" ]]; then
  echo "[backup-context] Obsidian vault not found at $VAULT_PARENT — skipping backup." >&2
  exit 0
fi
mkdir -p "$VAULT"

# Debounce: skip if we ran very recently.
STATE_FILE="$VAULT/.last-backup"
now="$(date +%s)"
if [[ -f "$STATE_FILE" ]]; then
  last="$(cat "$STATE_FILE" 2>/dev/null || echo 0)"
  if [[ "$last" =~ ^[0-9]+$ ]] && (( now - last < DEBOUNCE_SECONDS )); then
    exit 0
  fi
fi

# Resolve the project root (hook env -> git -> cwd).
REPO_ROOT="${CLAUDE_PROJECT_DIR:-}"
if [[ -z "$REPO_ROOT" ]]; then
  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi
REPO_NAME="$(basename "$REPO_ROOT")"

# Secret / noise denylist applied to every rsync.
EXCLUDES=(
  --exclude '*.local.json'
  --exclude '.credentials*'
  --exclude '.last-backup'
  --exclude 'history*'
  --exclude 'projects/'        # Claude Code chat logs live under ~/.claude/projects/
  --exclude '*.bak.*'
  --exclude '.git/'
  --exclude 'node_modules/'
  --exclude 'worktrees/'
)

changed=0
run_rsync() { # src dest_dir
  local src="$1" dest="$2"
  [[ -e "$src" ]] || return 0
  mkdir -p "$dest"
  local out
  out="$(rsync -aL --delete --itemize-changes "${EXCLUDES[@]}" "$src" "$dest" 2>/dev/null || true)"
  [[ -n "$out" ]] && changed=$(( changed + $(printf '%s\n' "$out" | grep -c . || true) ))
}

# --- This repo's bundle -> claude_context/<repo>/ ---
REPO_DEST="$VAULT/$REPO_NAME"
for item in agents commands memory core global hooks settings.json README.md; do
  run_rsync "$REPO_ROOT/.claude/$item" "$REPO_DEST/.claude/"
done
run_rsync "$REPO_ROOT/CLAUDE.md" "$REPO_DEST/"

# --- User-global backbone -> claude_context/_global/ ---
GLOBAL_DEST="$VAULT/_global"
for item in agents commands skills CLAUDE.md; do
  run_rsync "$HOME/.claude/$item" "$GLOBAL_DEST/"
done

# Record run time (post-work, so a slow backup still debounces the next trigger).
echo "$now" > "$STATE_FILE"

# Append one changelog line (Obsidian-friendly markdown).
LOG="$VAULT/_backup-log.md"
[[ -f "$LOG" ]] || printf '# Claude context backup log\n\n' > "$LOG"
ts="$(date '+%Y-%m-%d %H:%M:%S')"
if (( changed > 0 )); then
  printf -- '- %s  **%s**  (%s)  %d file(s) changed\n' "$ts" "$REPO_NAME" "$TRIGGER" "$changed" >> "$LOG"
else
  printf -- '- %s  **%s**  (%s)  no change\n' "$ts" "$REPO_NAME" "$TRIGGER" >> "$LOG"
fi

exit 0
