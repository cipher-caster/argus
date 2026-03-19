# /review — Argus System Review & Learning Loop

**Usage:**
- `/review` — full review: trading state, docs, memory, plan
- `/review trading` — trading logs and signal pipeline health only
- `/review docs` — documentation freshness check only
- `/review plan` — skip review, jump to planning next steps

---

## How to Execute This Skill

The argument is: `$ARGUMENTS`

Parse `$ARGUMENTS`:
- If empty → run **Full Review** (all sections A–E)
- `trading` → run sections A + B only
- `docs` → run sections C + D only
- `plan` → read memory + knowledge.md, then jump to section E

Backend base URL: http://localhost:8000
If backend is down: `docker-compose up -d`

**IMPORTANT:** Deploy agents in parallel for independent sections. Use Sonnet agents for speed. Compile findings at the end.

---

## Section A — Trading Pipeline Health

Check signal flow end-to-end. Deploy an agent to run these:

1. **Signal counts by source and outcome:**
   ```
   GET /api/analytics/signal-log?limit=500
   ```
   From the response, count:
   - Total signals, grouped by source (live / scanner / backtest)
   - OPEN signals (should have some if market gates aren't blocking)
   - Resolved signals: WIN / LOSS / REVIEW counts and win rate

2. **Paper trading state:**
   ```
   GET /api/trading/positions?status=OPEN,PENDING
   GET /api/trading/stats
   GET /api/trading/config
   ```
   Check:
   - Is trading enabled?
   - Any open/pending positions? If zero and trading is enabled, something may be wrong
   - Win rate and total trades from stats

3. **Signal-to-trade pipeline:**
   - If there are OPEN signals but zero positions → `execute_signals` may not be running or filtering them out
   - If there are positions but zero closed trades → positions may be stuck (check manage_positions job)
   - If trading is disabled → note it, don't flag as broken

4. **Optimization state:**
   ```
   GET /api/optimization/experiments?limit=5
   GET /api/optimization/best
   ```
   - How many experiments exist?
   - What's the current best config?
   - When was the last sweep run?

### Output format for Section A:
```
### Trading Pipeline Health

| Stage | Count | Status |
|-------|-------|--------|
| Backtest signals | {N} | {OK / note} |
| Live signals (OPEN) | {N} | {OK if >0, WARN if 0} |
| Scanner signals (OPEN) | {N} | {OK if >0, WARN if 0} |
| Resolved (W/L/R) | {W}/{L}/{R} | WR: {X}% |
| Paper positions | {N open} / {N pending} | {OK / WARN} |
| Closed trades | {N} | WR: {X}% |
| Optimization experiments | {N} | Last: {date} |

**Pipeline verdict:** {HEALTHY / PARTIAL / BROKEN — one sentence}
```

---

## Section B — Worker & Config Check

Read these files to verify worker job scheduling:

1. Read `backend/app/worker.py` — check cron schedules for:
   - `log_watchlist_setups` (should be 4H candle closes)
   - `log_best_setups` (should be every 5 min)
   - `resolve_signal_outcomes` (should be every 30 min)
   - `execute_signals` (should be at 4H candle closes)
   - `manage_positions` (should be every 5 min)

2. Check signal log config:
   ```
   Read backend/app/jobs/signal_log.py — check DEFAULT_WATCHLIST, DEFAULT_MIN_TITAN_CONFIDENCE
   ```

3. Check trading config defaults:
   ```
   Read backend/app/trading/orchestrator.py — check DEFAULT_TRADING_CONFIG
   ```

Flag anything that looks misconfigured or misaligned with `docs/trading/knowledge.md` best config.

---

## Section C — Documentation Freshness

Deploy an agent to check these docs for staleness:

1. **CHANGELOG** (`docs/CHANGELOG.md`):
   - Read the latest version entry
   - Compare with `git log --oneline -20` — are recent commits reflected?
   - If the last changelog entry is >3 days old and there are new commits, flag it

2. **CLAUDE.md** (root):
   - Check version number matches CHANGELOG
   - Check slash commands section lists all commands in `.claude/commands/`
   - Check architecture description matches current backend structure

3. **ROADMAP** (`docs/ROADMAP.md`):
   - Check completed phases match what's actually shipped
   - Check planned phases are realistic and not stale

4. **AI_AGENT_GUIDE** (`docs/AI_AGENT_GUIDE.md`):
   - Check "Current Limitations" — are any listed limitations now resolved?
   - Check "Recent Improvements" — does it cover the latest version?

5. **Backend Architecture** (`docs/backend/ARCHITECTURE.md`):
   - Does it mention all major modules? (routes, trading, jobs, strategies, indicators)

6. **Knowledge Base** (`docs/trading/knowledge.md`):
   - When was it last updated?
   - Does it reflect the latest optimization experiments from the DB?

### Output format for Section C:
```
### Documentation Freshness

| Document | Version/Date | Status | Action Needed |
|----------|-------------|--------|---------------|
| CHANGELOG | v{X} | {CURRENT / STALE} | {none / add vX.Y entry} |
| CLAUDE.md | v{X} | {CURRENT / STALE} | {none / update X} |
| ROADMAP | Phase {N} | {CURRENT / STALE} | {none / mark Phase N done} |
| AI_AGENT_GUIDE | — | {CURRENT / STALE} | {none / fix limitations} |
| Backend ARCH | — | {CURRENT / STALE} | {none / add module X} |
| knowledge.md | {date} | {CURRENT / STALE} | {none / add latest sweep} |
```

---

## Section D — Memory Review

Read all memory files in the memory directory (`/home/mjm/.claude/projects/-home-mjm-Documents-projects-argus/memory/`):

1. Read `MEMORY.md` index
2. Read each referenced memory file
3. For each, check:
   - Is the information still accurate given the current codebase?
   - Are there any file paths or function names that no longer exist?
   - Should any memory be updated or removed?
   - Is there new information from this review that should be saved?

Only flag memories that are **wrong** — memories that are simply incomplete are fine (they'll get updated naturally).

---

## Section E — Plan Next Steps

Based on all findings from sections A–D, create a prioritized plan:

### Priority 1: Critical (broken pipeline, wrong data)
Things that are actively broken or producing wrong results.

### Priority 2: Stale (docs, memory, config drift)
Things that work but don't reflect current state — creates confusion.

### Priority 3: Improvements (optimization, new features)
Things that would make the system better but aren't broken.

For each item, specify:
- What needs to change
- Which file(s) to edit
- Estimated scope (1-liner, small edit, new feature)

End with a clear recommendation: "Start with X" — the single most impactful thing to do next.

---

## After the Review

1. If any docs need updating, ask the user if they want you to fix them now (deploy agents in parallel for speed).
2. If any pipeline issues are found, offer to investigate and fix.
3. If trading knowledge has new findings, append to `docs/trading/knowledge.md`.
4. Update memory files if any are stale.
5. If everything is healthy, say so and suggest running `/optimize` or `/read market` for the next productive step.
