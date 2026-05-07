#!/usr/bin/env bash
# Argus — install Claude Code project memory into your local user-level Claude dir.
#
# Why this exists:
#   Claude Code reads project memory from ~/.claude/projects/<hashed-path>/memory/
#   where <hashed-path> is the absolute repo path with all `/` replaced by `-`
#   (with a leading dash). The repo can't ship files there directly because the
#   path depends on where each user clones.
#
#   This script computes the right path, then symlinks it to .claude/memory in
#   the repo. After that, edits to memory files are tracked in git and shared
#   across machines.
#
# Usage:
#   bash .claude/install.sh          # symlink (recommended — edits flow to repo)
#   bash .claude/install.sh --copy   # copy once instead of symlinking

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/.claude/memory"

if [[ ! -d "$SRC" ]]; then
  echo "ERROR: $SRC does not exist. Run from the Argus repo root." >&2
  exit 1
fi

# Compute the hashed-path dir Claude Code uses for this project.
HASH_NAME="$(echo "$REPO_ROOT" | sed 's|/|-|g')"
TARGET_PARENT="$HOME/.claude/projects/$HASH_NAME"
TARGET="$TARGET_PARENT/memory"

mkdir -p "$TARGET_PARENT"

if [[ -e "$TARGET" || -L "$TARGET" ]]; then
  echo "Existing $TARGET found."
  read -r -p "Back up to ${TARGET}.bak and replace? [y/N] " ans
  case "$ans" in
    y|Y|yes)
      mv "$TARGET" "${TARGET}.bak.$(date +%s)"
      ;;
    *)
      echo "Aborted. No changes made."
      exit 1
      ;;
  esac
fi

if [[ "${1:-}" == "--copy" ]]; then
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
