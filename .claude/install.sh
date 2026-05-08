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
# Usage:
#   bash .claude/install.sh                  # symlink memory (recommended)
#   bash .claude/install.sh --copy           # copy memory once instead of symlinking
#   bash .claude/install.sh --with-global    # also install user-global CLAUDE.md
#   bash .claude/install.sh --global-only    # only install global, skip memory
#   bash .claude/install.sh --copy --with-global  # combine

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/.claude/memory"
GLOBAL_SRC="$REPO_ROOT/.claude/global/CLAUDE.md"
GLOBAL_DST="$HOME/.claude/CLAUDE.md"

MODE="symlink"
DO_GLOBAL=0
DO_MEMORY=1

for arg in "$@"; do
  case "$arg" in
    --copy) MODE="copy" ;;
    --with-global) DO_GLOBAL=1 ;;
    --global-only) DO_GLOBAL=1; DO_MEMORY=0 ;;
    -h|--help) sed -n '14,20p' "$0"; exit 0 ;;
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

if [[ $DO_MEMORY -eq 0 ]]; then
  install_global
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
