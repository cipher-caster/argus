# /test-phase-c — Trading Analytics Integration (C1)

**Usage:**
- `/test-phase-c` — Run analytics integration tests (signal-position joins, regime capture, backtest dedup)

---

## How to Execute This Skill

Phase C tests close the feedback loop: connect signal outcomes to actual position P&L, capture regime state at resolution, deduplicate redundant analytics.

### C1: Trading Analytics Integration

**Root Issues:**
- Signal log captures market state at **fire time** but not at **resolution time** → can't correlate regime changes to outcomes
- Signal-position disconnect → no analytics query joins signal outcomes to actual position P&L
- Backtest tab in analytics is redundant with SignalLog's "Backtest" source filter → duplication

**Tests to Implement:**

1. **Signal-Position Join**
   ```bash
   docker compose exec backend pytest tests/test_analytics_integration.py::TestSignalPositionJoin -v
   ```
   - `test_signal_fires_creates_position` — signal outcome resolves with linked position P&L
   - `test_backtest_signal_matches_position_outcome` — backtest WIN/LOSS matches position realized PnL
   - `test_regime_at_resolution_captured` — regime state logged at resolution time
   - `test_btc_price_at_resolution_captured` — BTC price at resolution logged for regime correlation

2. **Backtest Tab Deduplication**
   ```bash
   docker compose exec backend pytest tests/test_analytics_dedup.py -v
   ```
   - Remove "Backtest" tab, filter SignalLog by source="backtest" instead
   - Verify analytics dashboard still renders leaderboard

3. **Rejected Signal Persistence**
   - Log rejected signals (low conviction, exposure cap, volatility gate) to DB
   - Enable rejection pattern analysis in analytics
   - Tests: `test_rejected_signal_persisted`, `test_rejection_reason_stored`, `test_analytics_rejection_rates`

## Full Phase C Validation

```bash
docker compose exec backend pytest tests/test_analytics_integration.py tests/test_analytics_dedup.py tests/test_rejected_signals.py -v --tb=short
```

**Target:** 7 new tests + data model updates (regime_at_resolution, btc_price_at_resolution, rejected_signals table)

**Why:** Currently can't correlate regime changes to trade outcomes or analyze rejection patterns. Backtest tab duplicates SignalLog filtering.

**Impact:** Enables trading performance feedback loop — learn which regimes/conditions lead to wins.
