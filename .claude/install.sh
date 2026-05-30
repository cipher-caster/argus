#!/usr/bin/env bash
# Argus — install Claude Code project memory (and optional global rules) into your local Claude dir.
#
# Why this exists:
#   Claude Code reads project memory from ~/.claude/projects/<hashed-path>/memory/
#   where <hashed-path> is the absolute repo path with all `/` replaced by `-`
#   (with a leading dash). The repo can't ship files there directly because the
#   path depends on where each user clones.
#
#   This script computes the right path, then symlinks .claude/memory into it.
#   After that, edits to memory files are tracked in git and shared across
#   machines. The optional --with-global flag also installs the user-global
#   CLAUDE.md (subagent model policy etc.) to ~/.claude/CLAUDE.md.
#
#   --with-core installs the portable agent-orchestration backbone: it symlinks
#   each file in .claude/core/agents and .claude/core/commands into your
#   user-global ~/.claude/agents and ~/.claude/commands (per-file, so unrelated
#   user agents/commands are left intact). After that the generic dev agents
#   (implementer, test-runner, diff-reviewer, debugger) and drivers (/dev, /fix,
#   /discuss) are available in EVERY project, and edits flow through git.
#
# Usage:
#   bash .claude/install.sh                  # symlink memory (recommended)
#   bash .claude/install.sh --copy           # copy memory once instead of symlinking
#   bash .claude/install.sh --with-global    # also install user-global CLAUDE.md
#   bash .claude/install.sh --with-core      # also install the portable orchestration backbone
#   bash .claude/install.sh --global-only    # only install global, skip memory
#   bash .claude/install.sh --copy --with-global --with-core  # combine

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/.claude/memory"
GLOBAL_SRC="$REPO_ROOT/.claude/global/CLAUDE.md"
GLOBAL_DST="$HOME/.claude/CLAUDE.md"

MODE="symlink"
DO_GLOBAL=0
DO_MEMORY=1
DO_CORE=0

for arg in "$@"; do
  case "$arg" in
    --copy) MODE="copy" ;;
    --with-global) DO_GLOBAL=1 ;;
    --with-core) DO_CORE=1 ;;
    --global-only) DO_GLOBAL=1; DO_MEMORY=0 ;;
    -h|--help) sed -n '14,30p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $arg" >&2; exit 1 ;;
  esac
done

install_global() {
  if [[ ! -f "$GLOBAL_SRC" ]]; then
    echo "WARN: $GLOBAL_SRC missing — skipping global install." >&2
    return
  fi
  mkdir -p "$(dirname "$GLOBAL_DST")"
  if [[ -e "$GLOBAL_DST" || -L "$GLOBAL_DST" ]]; then
    echo "Existing $GLOBAL_DST found."
    read -r -p "Back up to ${GLOBAL_DST}.bak.<ts> and replace? [y/N] " ans
    case "$ans" in
      y|Y|yes) mv "$GLOBAL_DST" "${GLOBAL_DST}.bak.$(date +%s)" ;;
      *) echo "Skipped global install."; return ;;
    esac
  fi
  cp "$GLOBAL_SRC" "$GLOBAL_DST"
  echo "Installed user-global rules: $GLOBAL_DST"
  echo "Note: this file applies across ALL your Claude Code projects, not just Argus."
}

# Per-file symlink each core agent/command into ~/.claude so the portable backbone
# is available in every project. Per-file (not whole-dir) so unrelated user
# agents/commands are left intact.
link_core_dir() { # <src_dir> <dst_dir> <label>
  local src_dir="$1" dst_dir="$2" label="$3"
  [[ -d "$src_dir" ]] || { echo "WARN: $src_dir missing — skipping $label." >&2; return; }
  mkdir -p "$dst_dir"
  local f base dst
  for f in "$src_dir"/*; do
    [[ -e "$f" ]] || continue
    base="$(basename "$f")"
    dst="$dst_dir/$base"
    if [[ -L "$dst" ]]; then
      ln -sf "$f" "$dst"            # refresh an existing symlink in place
    elif [[ -e "$dst" ]]; then
      mv "$dst" "${dst}.bak.$(date +%s)"
      ln -s "$f" "$dst"
      echo "  backed up existing $base -> ${base}.bak.<ts>"
    else
      ln -s "$f" "$dst"
    fi
    echo "  linked $label/$base"
  done
}

install_core() {
  local core="$REPO_ROOT/.claude/core"
  if [[ ! -d "$core" ]]; then
    echo "WARN: $core missing — skipping core backbone install." >&2
    return
  fi
  echo "Installing portable orchestration backbone (--with-core):"
  link_core_dir "$core/agents"   "$HOME/.claude/agents"   "agents"
  link_core_dir "$core/commands" "$HOME/.claude/commands" "commands"
  echo "Backbone installed. Verify: ls -la \"$HOME/.claude/agents\" \"$HOME/.claude/commands\""
  echo "Note: these apply across ALL your Claude Code projects."
}

if [[ $DO_MEMORY -eq 0 ]]; then
  install_global
  [[ $DO_CORE -eq 1 ]] && { echo; install_core; }
  exit 0
fi

if [[ ! -d "$SRC" ]]; then
  echo "ERROR: $SRC does not exist. Run from the Argus repo root." >&2
  exit 1
fi

HASH_NAME="$(echo "$REPO_ROOT" | sed 's|/|-|g')"
TARGET_PARENT="$HOME/.claude/projects/$HASH_NAME"
TARGET="$TARGET_PARENT/memory"

mkdir -p "$TARGET_PARENT"

if [[ -e "$TARGET" || -L "$TARGET" ]]; then
  echo "Existing $TARGET found."
  read -r -p "Back up to ${TARGET}.bak.<ts> and replace? [y/N] " ans
  case "$ans" in
    y|Y|yes) mv "$TARGET" "${TARGET}.bak.$(date +%s)" ;;
    *) echo "Aborted. No changes made."; exit 1 ;;
  esac
fi

if [[ "$MODE" == "copy" ]]; then
  cp -r "$SRC" "$TARGET"
  echo "Copied $SRC -> $TARGET"
  echo "Note: future edits will NOT sync back to the repo. Use the default symlink mode for that."
else
  ln -s "$SRC" "$TARGET"
  echo "Symlinked $TARGET -> $SRC"
  echo "Edits to .claude/memory/*.md will now be picked up by Claude Code automatically."
fi

echo
echo "Verify:  ls -la \"$TARGET\""

if [[ $DO_GLOBAL -eq 1 ]]; then
  echo
  install_global
fi

if [[ $DO_CORE -eq 1 ]]; then
  echo
  install_core
fi
