# Argus Project Memory Index

## User
- [user_trading_philosophy.md](user_trading_philosophy.md) — Swing trader, prefers market condition filtering, data-driven decisions

## Feedback
- [feedback_argus_best_practices.md](feedback_argus_best_practices.md) — Project-specific rules: gate parity, config precedence, schemas, caching, tests
- [feedback_audit_vs_closed_experiment.md](feedback_audit_vs_closed_experiment.md) — Audit recs never override closed-experiment memories without backtest evidence
- [feedback_backtest_before_deploy.md](feedback_backtest_before_deploy.md) — Always run backtest script to validate strategy changes before deploying
- [feedback_docker_no_build.md](feedback_docker_no_build.md) — Never use `--build` flag by default, build separately
- [feedback_docs_not_obsidian.md](feedback_docs_not_obsidian.md) — Log findings in docs/ folder, not Obsidian
- [feedback_proactive_review_skill.md](feedback_proactive_review_skill.md) — Proactively create meta-skills for review/docs/learning after shipping features
- [feedback_tests_before_code.md](feedback_tests_before_code.md) — Always check and update existing tests before implementing code changes
- [feedback_no_market_editorializing.md](feedback_no_market_editorializing.md) — Don't make macro market calls beyond what Argus data supports
- [feedback_sonnet_agents.md](feedback_sonnet_agents.md) — Subagent model policy: haiku/sonnet/opus by task complexity (global rule in ~/.claude/CLAUDE.md)
- [feedback_observation_before_prod.md](feedback_observation_before_prod.md) — Always require observation period with profitability proof before deploying trading changes
- [feedback_scanner_v1_bias.md](feedback_scanner_v1_bias.md) — Scanner WR on small samples is unreliable; always run full walkforward before adding a coin to the watchlist

## Project
- [project_current_version.md](project_current_version.md) — v1.1.4 — Execution-Layer Defense-in-Depth & Staleness Gate; 15-coin watchlist
- [project_okx_default_provider.md](project_okx_default_provider.md) — OKX is the default trading provider; Binance fallback removed
- [project_strategy_findings.md](project_strategy_findings.md) — Oracle removed from UI, regime detection active, Titan primary; SYMBOL_OVERRIDES removed
- [project_phase11_signal_log.md](project_phase11_signal_log.md) — Signal log with regime filtering, candle-walk resolution, 3 signal sources
- [project_paper_trading_engine.md](project_paper_trading_engine.md) — Paper trading engine: positions, risk gates, orchestrator, optimization system
- [project_analytics_redesign.md](project_analytics_redesign.md) — Analytics page is 2 tabs (Best Setups, Signal Log); Backtest Performance and WinRateTrend removed
- [project_phase19_plan.md](project_phase19_plan.md) — Phase 19 (WinRateTrend) shipped in v1.1.0 then removed end-to-end; do not re-implement
- [project_risk_rollback_history.md](project_risk_rollback_history.md) — 7% risk was tried 2026-04-05 and reverted to 3%; don't re-propose without new evidence
- [project_conviction_experiment.md](project_conviction_experiment.md) — Closed 2026-04-20: min_conviction set to 56; 2026-05-07 audit tried 56→60 again, reverted
- [project_post_conviction_review.md](project_post_conviction_review.md) — Closed 2026-04-20: APTUSDT removed, block_btc_sell deleted; ADX gate + ATOMUSDT swap deferred
- [project_orchestration_backbone.md](project_orchestration_backbone.md) — Portable .claude/core backbone: generic dev agents + /dev /fix /discuss drivers + Obsidian context backup
- [project_backend_cleanup_2026_06.md](project_backend_cleanup_2026_06.md) — Jun 2026 phased backend cleanup: what shipped + deferred backlog (broad-excepts, candle-walk merge, lint ratchet) + reusable backtest parity-gate procedure

## Reference
- [reference_backtest_docs.md](reference_backtest_docs.md) — Full backtest results and strategy docs location
