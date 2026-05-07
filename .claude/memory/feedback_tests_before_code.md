---
name: Tests before code changes
description: Always check and update existing tests before implementing code changes
type: feedback
---

When implementing changes, always check for existing tests first and update them before modifying the production code.

**Why:** User explicitly requested this workflow — ensures test coverage stays accurate and regressions are caught. Tests serve as documentation of expected behavior.

**How to apply:** For every code change: (1) find existing tests for the affected code, (2) update/add tests to cover the new behavior, (3) run tests to confirm they fail as expected, (4) implement the production code change, (5) run tests again to confirm they pass.
