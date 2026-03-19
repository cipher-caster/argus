Run a trading optimization loop for the Argus paper trading engine.

Usage: /optimize [sweep sl|tp|confidence|gates|full] [analyze] [apply] [status]

Backend base URL: http://localhost:8000
If backend is down: `docker-compose up -d`

---

## Default (no args) — Full Optimization Loop

1. **Read** `docs/trading/knowledge.md` for previous findings and dead ends
2. **GET** /api/trading/analysis → analyze closed paper trades
3. **GET** /api/trading/analysis/recommendations → get config suggestions
4. Based on the recommendations, pick the best sweep preset:
   - If conviction split is notable → `confidence_sweep`
   - If WR diverges from backtest → `sl_sweep` or `full_grid`
   - If a market state is losing → `gate_sweep`
   - Default: `sl_sweep` if no strong signal
5. **Run**: `docker compose exec -T backend python scripts/optimize_trading.py --preset={X}`
6. **GET** /api/optimization/experiments?run_id={latest_run_id} → compare results
7. If best EV/trade > current best by 10%+: **POST** /api/optimization/apply `{"experiment_id": N}`
8. **Append** findings to `docs/trading/knowledge.md` with the date, run_id, table of results, and a 1-2 sentence decision note
9. Present a before/after summary

---

## Subcommands

### /optimize sweep sl
Run SL multiplier sweep: [1.0, 1.25, 1.5, 1.75, 2.0, 2.5] × ATR
```
docker compose exec -T backend python scripts/optimize_trading.py --preset=sl_sweep
```

### /optimize sweep tp
Run TP multiplier sweep: [adaptive, 1.5, 2.0, 2.5, 3.0, 3.5] × ATR
```
docker compose exec -T backend python scripts/optimize_trading.py --preset=tp_sweep
```

### /optimize sweep confidence
Run min_titan_confidence sweep: [50, 55, 60, 65, 70, 75]
```
docker compose exec -T backend python scripts/optimize_trading.py --preset=confidence_sweep
```

### /optimize sweep gates
Run market gate permutations: {block_sleeping, macro_guard, strict_macro}
```
docker compose exec -T backend python scripts/optimize_trading.py --preset=gate_sweep
```

### /optimize sweep full
Run full grid: top-3 SL × top-3 TP × top-2 confidence (~18 configs, ~10-15 min)
```
docker compose exec -T backend python scripts/optimize_trading.py --preset=full_grid
```

### /optimize analyze
Show trade analysis and recommendations without running a sweep:
1. GET /api/trading/analysis
2. GET /api/trading/analysis/recommendations
3. GET /api/trading/analysis/report
Present patterns, any divergence from backtest, and suggested actions.

### /optimize apply
Show current best experiment and apply it:
```
docker compose exec -T backend python scripts/optimize_trading.py --apply-best
```
Or apply a specific experiment:
```
POST /api/optimization/apply {"experiment_id": N}
```

### /optimize status
Show recent experiments ranked by EV/trade:
```
GET /api/optimization/experiments?limit=20
GET /api/optimization/best
```
Display as a ranked table. Highlight the current production config (is_production=true).

---

## Knowledge Base

Always read `docs/trading/knowledge.md` before running sweeps to avoid re-testing dead ends.
Always append findings to that file after each run.

Format for appended entries:
```
### {date} — {preset_name}
- **Run ID**: {run_id}
- **Finding**: {1-2 sentences}
- **Table**: | Config | WR | Total R | EV/trade |
- **Decision**: {applied / not applied, reason}
```
