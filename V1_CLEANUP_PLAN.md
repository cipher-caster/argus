# Argus v1.0 Cleanup Plan

**Goal:** Freeze scope at v1.0. Remove dead code, half-removed surfaces, and stale docs. No new features.

**Source of truth:** four parallel audits run 2026-05-08 against branch `master` at commit `8d30c7a` (backend, frontend, tests, docs/config). All file:line references below come from those audits.

**Execution model:** each work item below is scoped to be handed to a single sub-agent. Items are ordered by risk: pure deletions first, code-with-callers next, behavior-changing cleanups last, docs last. Within each item: files touched, evidence, acceptance criteria, risk notes, and a ready-to-paste agent brief.

**Decisions still required from user** (resolve before starting items marked ⚠️):
- **D1 — Binance code:** Remove entirely (Items 11a/11b) or keep as runtime fallback (skip 11a/11b, only fix the historical-position default in 11c)? Default recommendation: **keep as fallback, fix the migration default**, since Binance is still wired into market-data routes that the dashboard uses.
- **D2 — Oracle backend:** Oracle is removed from UI but powers screener, BTC market gate, and best-setups enrichment in backtest_engine. Confirm we keep Oracle as a backend-only engine and only remove the orphaned `/api/strategy/oracle/{symbol}` HTTP route (Item 6). Recommendation: **keep Oracle backend, remove only the orphaned route**.
- **D3 — `macro_guard` / `block_sleeping` / `block_volatile` flags:** Live signal job ignores them but they're stored, exposed via API, and honored by backtest_engine. Drop from live config schema (Item 9), or wire them into the live job? Recommendation: **drop from live config schema** — backtest engine keeps its own copy.

---

## Phase 1 — Pure deletions (zero behavior risk)

### Item 1 — Delete empty / stray files

**Files:**
- `frontend/src/app/analytics/imports.ts` (0 bytes, no importers)
- `backend/debug_fvg.py`, `backend/test_fvg.py`, `backend/test_mss.py` (root-level dev scripts, not imported, not collected by pytest)
- `backend/tests/verify_freshness.py`, `backend/tests/verify_refactor.py` (asyncio dev scripts, no `def test_`, not collected by pytest)

**Acceptance:** files removed; `git grep` for each filename returns zero hits; `pytest --collect-only` count unchanged; `npm run build` passes.

**Agent brief:**
> Delete these 6 files outright. Verify nothing imports them by grepping each filename across the repo before deletion. After: run `cd frontend && npx tsc --noEmit` and `docker compose exec backend pytest --collect-only -q` and confirm both still work. Commit message: `chore(v1.0): remove empty/stray dev files`.

---

### Item 2 — Remove unused npm/pip dependencies

**Backend:** `backend/requirements.txt` line 15 — `websockets>=12.0` (zero imports under `backend/app/`).

**Frontend:** none found.

**Acceptance:** dep removed; `pip-compile` / image rebuild passes; `docker compose exec backend pytest -q` passes.

**Agent brief:**
> Remove the `websockets>=12.0` line from `backend/requirements.txt`. Confirm zero `import websockets` and `from websockets` hits across `backend/`. Rebuild the backend image and run the test suite. Commit message: `chore(v1.0): drop unused websockets dependency`.

---

### Item 3 — Delete `docs/ROADMAP.md` and update references

**Files:**
- Delete `docs/ROADMAP.md` (entire file).
- Edit `CLAUDE.md` line 104: remove the `docs/ROADMAP.md — Planned features` bullet from the Documentation list.

**Acceptance:** `git grep -i roadmap.md` returns only this plan and changelog history (if any).

**Agent brief:**
> Delete `docs/ROADMAP.md`. In `CLAUDE.md` find the Documentation bullet list and remove the line referencing `docs/ROADMAP.md`. Do not edit anything else. Commit message: `docs(v1.0): retire ROADMAP — scope frozen at v1.0`.

---

## Phase 2 — Frontend dead code (≈1,430 lines, no behavior change)

### Item 4 — Remove dead frontend components

**Files (delete):**
- `frontend/src/components/analytics/BacktestPerformance.tsx`
- `frontend/src/components/analytics/OracleSignalSummary.tsx`
- `frontend/src/components/analytics/OracleScreener.tsx`
- `frontend/src/components/analytics/ContrarianRadar.tsx`
- `frontend/src/components/analytics/MarketSentimentBar.tsx` (only consumer is `OracleSignalSummary`)
- `frontend/src/components/features/dashboard/StatsCards.tsx`
- `frontend/src/components/features/dashboard/MarketPulseStrip.tsx`
- `frontend/src/components/features/dashboard/TopCoinsWidgets.tsx`
- `frontend/src/components/features/dashboard/MarketIndicators.tsx`
- `frontend/src/components/features/dashboard/IndicatorCard.tsx` (only consumer is `MarketIndicators`)
- `frontend/src/components/common/SymbolSelector.tsx`

**Edit:**
- `frontend/src/components/analytics/index.ts` — remove exports for `BacktestPerformance` (line 1) and `OracleSignalSummary` (line 5).

**Evidence:** zero JSX usages found via grep. None of these are dynamically imported by `analytics/page.tsx` (which only loads `BestSetups` and `SignalLog`) or by any dashboard widget.

**Acceptance:** `npx tsc --noEmit` clean; `npm run build` clean; `npx playwright test` passes (after Item 7 which fixes the stale e2e test).

**Agent brief:**
> Delete the 11 component files listed in V1_CLEANUP_PLAN.md Item 4. Edit `frontend/src/components/analytics/index.ts` to remove the `BacktestPerformance` and `OracleSignalSummary` re-exports. Run `npx tsc --noEmit` and `npm run build` from `frontend/`. Do NOT run Playwright yet — there is a separate stale-test fix in Item 7 that must land first. Commit message: `chore(v1.0): remove dead frontend components`.

---

### Item 5 — Remove dead frontend hooks, API client functions, types

**Edit `frontend/src/lib/api.ts` — remove:**
- `AnalyticsSymbolsResponse` (lines 92–96) + `fetchAnalyticsSymbols` (163–168)
- `ScreenerItem`, `ScreenerResponse` (97–113) + `fetchOracleScreener` (170–175)
- `MeanReversionItem`, `MeanReversionResponse` (115–128) + `fetchMeanReversion` (177–182)
- `OracleSignalSummaryResponse` (130–137) + `fetchOracleSignalSummary` (184–186)
- `TitanRadarItem`, `TitanRadarResponse` (138–162) + `fetchTitanRadar` (226–228)
- Experiment block: `ExperimentParams`, `ExperimentResults`, `Experiment`, `fetchExperiments`, `fetchExperiment`, `fetchBestExperiment`, `applyExperiment` (302–358)
- `ProviderCoinStat`, `ProviderStats`, `ProviderComparisonResponse` (491–507) + `fetchProviderComparison` (508–510)

**Edit `frontend/src/hooks/useAnalyticsData.ts` — remove:**
- `useAnalyticsSymbols` (14–20)
- `useOracleScreener` (33–42)
- `useContrarianRadar` (45–54)
- `useOracleSignalSummary` (56–65)
- `useTitanRadar` (67–76)
- `useProviderComparison` (128–136)
- Adjust the import at line 8 to drop the now-unused `fetch*` symbols.

**Keep:** `useBacktestStats` (used by `CoinSignalIntel` + `CoinAnalysisModal`).

**Acceptance:** `npx tsc --noEmit` clean; no orphaned imports remain in `useAnalyticsData.ts`.

**Agent brief:**
> Edit `frontend/src/lib/api.ts` and `frontend/src/hooks/useAnalyticsData.ts` per V1_CLEANUP_PLAN.md Item 5. Preserve `useBacktestStats` and its `fetchBacktestStats` import. After edits, run `cd frontend && npx tsc --noEmit` — it must be clean. Then `npm run build`. Commit message: `chore(v1.0): remove dead analytics hooks and api functions`.

---

### Item 6 — Fix `prophet_strategy` ghost in indicator picker

**File:** `frontend/src/hooks/useIndicators.ts`

**Issue:** Lines 29–35 inject a `prophet_strategy` indicator definition; line 50 then filters it out before calculation. It appears in the picker but never produces output. Oracle was removed from UI.

**Edit:** Remove the `prophet_strategy` injection at 29–35 and drop the corresponding `i.type !== "prophet_strategy"` guard at line 50.

**Acceptance:** type check clean; indicator picker no longer lists `prophet_strategy`.

**Agent brief:**
> Edit `frontend/src/hooks/useIndicators.ts`. Remove the hardcoded `prophet_strategy` indicator entry at lines 29–35 and remove the `i.type !== "prophet_strategy"` filter at line 50. Verify by reading the file that no other reference to `prophet_strategy` remains in this hook. Run `cd frontend && npx tsc --noEmit`. Commit message: `chore(v1.0): drop dead prophet_strategy indicator entry`.

---

### Item 7 — Fix stale Playwright analytics test

**File:** `frontend/tests/e2e.spec.ts` lines 71–84.

**Issue:** Test asserts on `getByText("Futures Data")` and a `Funding Rate` button that no longer exist anywhere in the frontend source. Current analytics page has only 2 tabs: Best Setups and Signal Log.

**Edit:** Rewrite the test to assert on the actual analytics page surface — heading, two tab labels, a chart/table render. Or delete it if `data-rendering.spec.ts` already covers analytics.

**Acceptance:** `npx playwright test` green.

**Agent brief:**
> Open `frontend/tests/e2e.spec.ts` lines 71–84. Read `frontend/src/app/analytics/page.tsx` to see the actual rendered surface (2 tabs: `best-setups`, `signal-log`). Decide: rewrite the test to assert on the actual UI, OR delete the test if `frontend/tests/data-rendering.spec.ts` already exercises the analytics page (read it first to check). Run `cd frontend && npx playwright test` — must pass. Commit message: `test(v1.0): fix or remove stale analytics e2e assertions`.

---

## Phase 3 — Backend dead code (no behavior change)

### Item 8 — Remove dead helpers and exception classes

**Files:**
- `backend/app/jobs/signal_log.py` — delete `_get_btc_oracle_signal()` (176–186) and `_get_oracle_score()` (188–197). Zero callers.
- `backend/app/trading/backtest_engine.py:529` — delete the `btc_bias = btc_macro["bias"]` line; comment in code already flags it as unused.
- `backend/app/exceptions.py` — delete `ExecutionError` (62–72) and `RiskCheckError` (74–83). Never imported, never raised.
- `backend/app/exceptions.py` — `CacheError` (26–36) is caught but never raised. Audit catch sites in `routes/market.py` and `routes/indicators.py`; if all `except CacheError` blocks are unreachable, remove them and the class. If keeping for forward-compatibility, leave a `# raised by …` comment pointing at where it should be raised, or delete outright. **Default: delete the class and its catch sites.**

**Acceptance:** `pytest -q` passes; `docker compose up -d` healthy.

**Agent brief:**
> Make the deletions described in V1_CLEANUP_PLAN.md Item 8. For `CacheError`: grep for every `except CacheError` and `raise CacheError` site; if zero raises exist (expected), delete the class definition AND each catch block, leaving any peer `except DataProviderError` etc. intact. Run `docker compose exec backend pytest -q`. Commit message: `chore(v1.0): remove dead backend helpers and exceptions`.

---

### Item 9 — ⚠️ Drop ignored signal-log config flags (depends on D3)

**Files:**
- `backend/app/jobs/signal_log.py` — remove `macro_guard`, `block_sleeping`, `block_volatile` from the default config dict (around 138–140). Confirm `log_watchlist_setups` does not read them.
- `backend/app/schemas/analytics.py` lines ~93–95 — remove the corresponding `SignalLogConfig` fields.
- `frontend/src/lib/api.ts` and any UI form bound to these fields — drop them.
- Tests: update any test fixture that sets these keys.

**Acceptance:** PUT `/api/analytics/signal-log/config` no longer accepts the dropped keys (or accepts and ignores them with a deprecation note — pick one). Backtest engine unaffected (it has its own `BacktestConfig` and is allowed to honor these as before).

**Agent brief:**
> Only proceed if user has confirmed D3=drop. Edit the three files in V1_CLEANUP_PLAN.md Item 9. Search the repo for any test or frontend form referencing `macro_guard`, `block_sleeping`, or `block_volatile` in the signal-log context (NOT backtest engine — those usages stay). Remove them. Run backend pytest and frontend `npx tsc --noEmit`. Commit message: `chore(v1.0): drop ignored signal-log config flags`.

---

### Item 10 — Remove orphaned HTTP routes (depends on D2)

**Files:**
- `backend/app/routes/strategy.py` lines 129–171 — delete `GET /api/strategy/oracle/{symbol}` route handler. No frontend caller. Keep the `oracle` singleton import — `routes/analytics.py:28` re-imports it (`from app.routes.strategy import ..., oracle`). Better: move the `oracle = OracleStrategy()` singleton out of `routes/strategy.py` into `app/strategies/oracle.py` (e.g. a module-level `default_oracle`) and update both `routes/strategy.py` and `routes/analytics.py` imports. This breaks the surprise cross-module coupling.
- `backend/app/routes/analytics.py` lines 683–798 — `GET /api/analytics/signal-outcomes`. No frontend caller. Decide: delete, or keep as a backend-internal diagnostic endpoint. **Default: delete.**

**Acceptance:** routes removed from OpenAPI; pytest passes; frontend has no broken calls (none expected — confirmed dead).

**Agent brief:**
> Only proceed if user has confirmed D2=keep-Oracle-backend. Implement V1_CLEANUP_PLAN.md Item 10. Move the Oracle singleton out of `routes/strategy.py`, then delete the two routes. Update both `routes/strategy.py` and `routes/analytics.py` to import from the new location. Run `docker compose exec backend pytest -q`. Commit message: `refactor(v1.0): remove orphaned analytics/strategy routes, decouple oracle singleton`.

---

### Item 11 — ⚠️ Binance code path (depends on D1)

This is three sub-items because the audit found three distinct surfaces.

**11a — Remove BinanceProvider code (only if D1=remove-entirely):**
- Delete `backend/app/providers/binance_provider.py`.
- Edit `backend/app/providers/__init__.py` to drop the `BinanceProvider` export and the `if name == "binance": return BinanceProvider()` branch in `get_provider()`.
- Edit `backend/app/worker.py` line 9 + 48 — drop import and Binance branch in `get_active_provider()`.
- Edit `backend/app/routes/market.py` lines 153, 166 — `switch_provider` should reject `provider=binance` or be removed entirely if there are no other providers worth switching to.
- Edit `backend/app/routes/strategy.py` lines 22, 198 — drop `BinanceProvider` import and the `provider=binance` query handling.
- Edit `backend/app/trading/orchestrator.py` lines 336–339 — remove the Binance branch in `_provider_instance()`. Add a hard error if a position row has `provider='binance'` (since 11c will migrate them).

**11b — Drop unused `get_ticker_price()` (always safe, do regardless of D1):**
- `backend/app/providers/binance_provider.py:87` and `backend/app/providers/okx_provider.py:94` — both methods, zero callers.
- `backend/app/providers/data_provider.py:68` — abstract base method.
- If 11a is done, only the OKX one and the abstract need removing.

**11c — Fix the `migrate_v0_9_2.py` Binance default for historical positions (always do, regardless of D1):**
- Even with D1=keep-Binance-as-fallback, leaving historical position rows defaulted to `provider='binance'` causes the orchestrator to instantiate Binance at runtime when resolving those positions' candles. Either close out those rows or migrate them to `provider='okx'`. **Default: write a one-time migration that updates all `position` rows where `provider IS NULL OR provider='binance'` AND `status='closed'` to `provider='okx'` (so they don't reactivate Binance during candle re-resolution); leave any genuinely open Binance positions alone and surface them to the user.**
- New file: `backend/migrate_v1_0_0_okx_default.py`. Idempotent. Add a note in `docs/CHANGELOG.md`.

**Acceptance:** `pytest -q` passes; `docker compose up -d` healthy; `SELECT provider, status, count(*) FROM position GROUP BY 1,2;` shows no `binance` rows in `closed` status after migration.

**Agent brief (11b only — safe to start now):**
> Delete the `get_ticker_price` method from `backend/app/providers/okx_provider.py` and `backend/app/providers/binance_provider.py`, and the abstract declaration in `backend/app/providers/data_provider.py:68`. Confirm zero callers via repo-wide grep. Run `docker compose exec backend pytest -q`. Commit message: `chore(v1.0): drop unused get_ticker_price provider method`.

**Agent briefs for 11a / 11c:** to be drafted after D1 is decided.

---

### Item 12 — Drop dead `symbol` parameter in `calculate_risk_levels`

**File:** `backend/app/strategies/titan.py` lines 8–35.

**Issue:** `calculate_risk_levels(..., symbol=...)` accepts `symbol` but never reads it inside. Per-symbol overrides were removed; the parameter is now noise threaded through three callers (backtest_engine, signal_log, analytics).

**Edit:** Remove the `symbol` parameter from `calculate_risk_levels()` and its method version on `TitanStrategy`. Remove `symbol=` from each call site. Update the docstring.

**Acceptance:** pytest green; type-check happy; signal output unchanged on a smoke run.

**Agent brief:**
> Open `backend/app/strategies/titan.py`. Remove the `symbol` parameter from the module-level `calculate_risk_levels` (lines 8–35) and any `TitanStrategy._calculate_risk_levels` wrapper. Grep for `calculate_risk_levels(` and `_calculate_risk_levels(` repo-wide; remove `symbol=` (or positional symbol) from every caller. Run `docker compose exec backend pytest -q`. Confirm `tests/test_titan*.py` passes. Commit message: `refactor(v1.0): drop dead symbol param in calculate_risk_levels`.

---

## Phase 4 — Docs sweep

### Item 13 — Binance → OKX language sweep

**Files (with line refs from audit):**
- `README.md` lines 3, 12, 43 (per-symbol risk override sentence — DELETE), 66, 81 (test count — update), 111 (version — update to v1.1.4 going to v1.0.0 at release time)
- `CLAUDE.md` lines 7, 59, 68, 76 (drop `BacktestPerformance` from analytics panels list), 87
- `docs/AI_AGENT_GUIDE.md` lines 3 (Last Updated), 22, 36, 97–98, 194, 214–228 (delete the `schemas/validation.py` section — file deleted in v1.1.2), 360 (test count), 410–417 (WinRateTrend recent-improvement entry — remove or annotate), 452, 468 (3 tabs → 2 tabs)
- `docs/backend/ARCHITECTURE.md` lines 21, 49, 92 (mermaid + provider list), 97 (drop `log_contrarian_signals` row), 122–123 (drop `counter` source row), 189 (test count)
- `docs/frontend/ARCHITECTURE.md` lines 3 (Last Updated), 43, 54, 245 (`BacktestPerformance` listed as active — remove), 539 (E2E now exists)
- `docs/CHANGELOG.md` v1.1.0 entry — append a one-line "WinRateTrend was subsequently removed; do not re-implement" annotation; do not rewrite history.
- `docs/OKX_BACKTEST_REPORT.md` line 15 — annotate that Oracle is no longer in the live signal pipeline; the report describes historical backtest behavior.
- `docs/backend/ERROR_HANDLING.md` — optional cosmetic: change "Binance API" example to "exchange API". If `CacheError` is removed in Item 8, also remove it from the hierarchy doc here.

**Test counts:** run `docker compose exec backend pytest --collect-only -q | tail -1` and `cd frontend && npx playwright test --list | tail -1` to get fresh numbers — substitute everywhere.

**Acceptance:** every Binance reference in user-facing docs either says OKX, says "OKX (Binance kept as fallback)", or is gone. `BacktestPerformance` no longer described as active anywhere. Test counts current. Last Updated dates current.

**Agent brief:**
> Apply every doc edit in V1_CLEANUP_PLAN.md Item 13. Get the current backend pytest count via `docker compose exec backend pytest --collect-only -q | tail -1` and the playwright count via `cd frontend && npx playwright test --list | tail -1`; substitute those exact numbers. Update every "Last Updated" header to today's date (2026-05-08). After edits, grep `git grep -n -i "binance" docs/ README.md CLAUDE.md` and confirm every remaining hit is intentional (e.g., describing the kept fallback) — paste the residual list into the commit message body. Commit message: `docs(v1.0): sweep stale Binance/BacktestPerformance/test-count references`.

---

## Phase 4.5 — Test triage

### Item 13.5 — Prune non-relevant tests and retire test-phase scaffolds

**Rationale:** user has flagged that the suite carries tests that no longer pull their weight. The audit also found three slash commands (`/test-phase-a`, `-b`, `-c`) whose bodies still say "tests do not exist yet" even though backend now has 400+ tests. Treat these together.

**Step 1 — Inventory:**
- Run `docker compose exec backend pytest --collect-only -q | sort -u | head -200` to see the current set.
- Run `cd frontend && npx playwright test --list` for E2E.
- Compare against the dead-code findings in this plan: any test that exercises code being deleted in Items 4, 5, 6, 8, 10, 11, 12 should be deleted alongside its target.

**Step 2 — Prune by category:**
1. **Tests for already-removed surfaces** — already covered by the stale-tests audit (e.g. `test_oracle.py` stays valid only as long as Items 6/10 keep Oracle backend; if Oracle is fully retired post-v1.0, this file goes too).
2. **Over-mocked tests with no behavior coverage** — tests where every collaborator is mocked, so the test only verifies the mock setup. Identify by reading top of test files and looking for tests that touch only `Mock()` objects, never real DB / Redis / SQLAlchemy. Per `feedback_argus_best_practices.md`, integration tests must hit real surfaces.
3. **Trivial getter/setter coverage** — tests that just assert a default value or pass-through return. Low signal, high maintenance.
4. **Snapshot-style tests with no semantic check** — tests that assert exact JSON shape but never verify business logic.

**Step 3 — Retire test-phase commands:**
- `.claude/commands/test-phase-a.md`, `.claude/commands/test-phase-b.md`, `.claude/commands/test-phase-c.md` — three slash commands whose body says "tests do not exist yet" while the suite has long since grown past that. Either:
  - Rewrite each as a thin wrapper that runs the relevant subset (`pytest backend/tests/test_backtest_engine.py backend/tests/test_signal_log.py backend/tests/test_analyzer.py -q` for phase-a, etc.), OR
  - Delete all three.
- **Default: delete all three.** A single `/test` command (or just the user typing `pytest -q`) covers the use case. Adds three sources of confusion for no gain.

**Step 4 — Reconfirm coverage:**
- After deletions, run the full suite: `docker compose exec backend pytest -q && cd frontend && npx playwright test`.
- Generate a fresh count for Item 13's docs sweep.

**Acceptance:**
- Test count drops by a meaningful margin (target: at least 15-20% reduction without losing coverage of any v1.0 surface).
- All remaining tests pass.
- `/test-phase-{a,b,c}` slash commands no longer show in the available-skills list.

**Agent brief:**
> Implement V1_CLEANUP_PLAN.md Item 13.5. First, run `docker compose exec backend pytest --collect-only -q` and capture the test list. For each test, classify as KEEP, DELETE, or REVIEW based on the criteria in Step 2. Produce a punch list, get user approval before deleting (this is judgment-call territory). After approval, execute deletions, retire the three test-phase command files, run the full suite, report new test count. Use the code-reviewer subagent (`.claude/agents/code-reviewer.md`) to sanity-check the punch list before deleting. Commit message: `test(v1.0): prune non-relevant tests, retire test-phase scaffolds`.

---

## Phase 5 — Verification

### Item 14 — Full verification run

After all prior items land:

1. `docker compose up -d --build` (yes, build, since deps changed).
2. `docker compose exec backend pytest -q` — expect green.
3. `cd frontend && npx tsc --noEmit && npm run build && npx playwright test` — expect green.
4. Open http://localhost:3000, exercise: dashboard, analytics (both tabs), chart page, trading page. Manual sanity check.
5. Bump version: `docs/CHANGELOG.md` add v1.0.0 entry summarizing the cleanup; update version in `package.json` and any backend `__version__`.
6. Tag locally — do not push.

**Agent brief:**
> Run V1_CLEANUP_PLAN.md Item 14 verification steps. Report a punch list: any failing test, type error, runtime error, or broken UI surface. Do NOT push the tag — surface the result to the user for approval. Capture the version bump in `docs/CHANGELOG.md` with one-line summaries per phase from this plan.

---

## Risk register

| Risk | Mitigation |
|---|---|
| Removing Oracle singleton coupling breaks `analytics.py` import | Item 10 explicitly relocates the singleton before deleting the route. |
| Binance removal (11a) breaks historical position resolution | Item 11c migrates closed positions to `provider='okx'` first; orchestrator path becomes unreachable. |
| Stale Playwright test (Item 7) blocks Item 4 verification | Land Item 7 before running playwright after Item 4. |
| Test counts drift again before release | Capture counts at Item 13, lock in at Item 14. |
| Removing `CacheError` removes a catch site that silently swallowed a real error | Audit `except CacheError` blocks for what they're hiding before deletion; if any wraps a real risk path, leave the catch and document. |

---

## Item dependency graph

```
1, 2, 3            (independent, do first)
4 → 5 → 7          (frontend chain; 7 before any playwright run after 4)
6                  (independent frontend)
8                  (independent backend)
11b                (independent backend)
12                 (independent backend)
9                  (waits on D3)
10                 (waits on D2)
11a, 11c           (wait on D1)
13                 (waits on 4–12 so test counts and feature lists are accurate)
14                 (last)
```

Suggested execution order with one agent per item, in parallel where the graph allows: `[1, 2, 3, 8, 11b, 12]` → `[4, 6]` → `[5, 7]` → user decisions D1/D2/D3 → `[9, 10, 11a/c]` → `13` → `13.5` → `14`.
