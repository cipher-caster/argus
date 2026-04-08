#!/usr/bin/env bash
# Pre-commit checks for Argus.
# Wired up via .claude/settings.json as a PreToolUse hook on `git commit`.
# Runs tsc --noEmit on frontend changes and pytest --collect-only on backend changes.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

staged="$(git diff --cached --name-only --diff-filter=ACMR)"
if [[ -z "$staged" ]]; then
  exit 0
fi

frontend_changed=0
backend_changed=0
while IFS= read -r f; do
  case "$f" in
    frontend/*.ts|frontend/*.tsx|frontend/**/*.ts|frontend/**/*.tsx) frontend_changed=1 ;;
    backend/*.py|backend/**/*.py) backend_changed=1 ;;
  esac
done <<< "$staged"

if [[ $frontend_changed -eq 1 ]]; then
  echo "[pre-commit] frontend changes detected → npx tsc --noEmit"
  if ! (cd frontend && npx tsc --noEmit); then
    echo "[pre-commit] FAILED: frontend type check"
    exit 2
  fi
fi

if [[ $backend_changed -eq 1 ]]; then
  echo "[pre-commit] backend changes detected → pytest --collect-only"
  if ! docker compose exec -T backend pytest --collect-only -q; then
    echo "[pre-commit] FAILED: backend pytest collection"
    exit 2
  fi
fi

exit 0
