---
name: Log findings in docs/ not Obsidian
description: User wants strategy findings, backtest results, and experiment logs saved in the project docs/ folder, not external Obsidian notes
type: feedback
---

Log all findings, experiment results, strategy documentation, and skill output in `docs/` within the Argus project, not in Obsidian or external locations.

**Why:** User wants findings version-controlled alongside the code, accessible to anyone working on the project. Confirmed again 2026-03-24 when asked about Obsidian vs docs/ — chose docs/.

**How to apply:** When documenting backtest results, strategy changes, experiment findings, or market reports, write to the appropriate `docs/` subdirectory. Market reports go to `docs/market-reports/YYYY-MM-DD-{type}.md`. The main backtest doc is `docs/strategies/BACKTEST_RESULTS.md`.
