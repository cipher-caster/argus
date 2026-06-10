---
name: project_backend_cleanup_2026_06
description: "Backend cleanup (Jun 2026, branch chore/backend-cleanup) — what shipped + the deferred follow-up backlog"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3cb64539-6730-4bbf-b3b9-389566a0b5a1
---

Phased backend cleanup completed 2026-06-10 on branch `chore/backend-cleanup` (7 commits off master). All behavior-preserving; full suite stayed green (433 → 431, only 2 redundant tests removed). Closed-experiment guards untouched (3% risk, conviction 56, 15-coin watchlist, OKX).

**Shipped:** ruff lint+format tooling (`backend/pyproject.toml`, was a blank slate); dead-code/hygiene removal; centralized constants (`FEE_PCT`, `REGIME_CACHE_KEY/TTL`, `SIGNAL_LOG_CONFIG_KEY`, `CANDLE_4H_MS`); type modernization + `providers.provider_for()` factory dedup; shared `gross_pnl_usd()` + `tp_sl_hit()` helpers in `app/utils/trading_utils.py`; redundant-test removal with SMC tests relocated into `tests/test_calculator.py`.

**Deferred follow-ups (NOT done — each needs its own focused pass):**
- **Broad `except Exception` (~76, ruff B904)** — narrow to the `exceptions.py` hierarchy + add `raise ... from`. Behavior-changing (catch surface / swallow semantics), case-by-case. Biggest remaining gap vs CLAUDE.md's "raise from the hierarchy" rule.
- **Full candle-walk state-machine merge** — the 3 TP/SL walk loops (orchestrator, signal_log historical, backtest_engine) still duplicate the loop; only the per-candle predicate was extracted. signal_log's has a `sig.tp>0` guard the others lack — do NOT blindly unify.
- **The two 5m tiebreakers** (`signal_log._resolve_tiebreaker_5m` vs `backtest_engine._tiebreaker_5m_from_db`) — same algorithm, different data access; still duplicated.
- **Regime-fallback dedup** — orchestrator has 2 inline copies of the `signal-summary → market:regime → UNKNOWN` pattern; NOT merged into `signal_log._get_market_state` because missing-key/empty-regime semantics differ subtly (`regime_data.get("regime","UNKNOWN")` vs `if regime_data.get("regime")`).
- **Outcome-model inconsistency** — orchestrator.check_open + backtest use tp/sl-hit to set WIN/LOSS; signal_log fast-path + manual_close use `pnl_usd >= 0`. Genuinely different semantics; harmonizing is a behavior change needing evidence, not a refactor.
- **`_price_round` unification** — flat `round(x,6)` collapses sub-cent TP/SL; only worth doing if a watchlist coin is sub-cent priced (none were at time of writing). Evidence-gated bugfix, not parity.
- **Ratcheted-off lint rules** in `pyproject.toml` ignore list (F841, E402, E741, E712, SIM105/108/117/202, B007/B023/B905, B904) — remove each code as its violations are fixed.

See [[feedback_backtest_before_deploy]], [[project_paper_trading_engine]].

**Reusable: trading dedup parity-gate procedure.** To prove a refactor of trading/backtest logic is behavior-preserving: (1) `docker compose stop worker` to freeze the DB candle set; (2) `docker compose exec -T backend python scripts/run_signal_backtest.py --symbols=BTC,ETH,... --dry-run --fix-optimal` with **bare tickers** (script builds `{coin}/USDT`; passing `BTCUSDT` silently yields zero signals); (3) diff before/after output — must be byte-identical; (4) restart worker after. Worker is `build:`-based, so `docker compose start worker` runs the OLD image until rebuilt (inert for behavior-preserving changes). Anchor baseline at time of writing: 566 signals, 53.36% WR, +135.0R.
