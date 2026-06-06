# /test-analytics — Trading Analytics Integration

**Usage:**
- `/test-analytics` — Run analytics integration tests (signal-position joins, regime capture, backtest dedup)

---

## How to Execute This Skill

These tests cover the analytics feedback loop: connecting signal outcomes to actual position P&L, capturing regime state at resolution, and deduplicating redundant analytics.

What they validate:
- Signal log captures market state at both fire time and resolution time, so regime changes can be correlated to outcomes
- Analytics queries join signal outcomes to actual position P&L
- The analytics "Backtest" view reuses the SignalLog `source="backtest"` filter rather than duplicating it

Run these:

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

## Full Validation

```bash
docker compose exec backend pytest tests/test_analytics_integration.py tests/test_analytics_dedup.py tests/test_rejected_signals.py -v --tb=short
```

Covers the data model for `regime_at_resolution`, `btc_price_at_resolution`, and the `rejected_signals` table — enabling correlation of regime changes to trade outcomes and analysis of rejection patterns.
