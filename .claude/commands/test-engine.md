# /test-engine — Trading Engine Safety Net

**Usage:**
- `/test-engine` — Run the trading-engine tests (backtest engine, historical resolution, TradeAnalyzer)

---

## How to Execute This Skill

These tests guard against silent regressions in the core trading engine:
- Backtest engine unit tests (WIN/LOSS/REVIEW outcomes, conviction filter, stats)
- Historical outcome resolution (candle-walk TP/SL edge cases, no-data fallback)
- TradeAnalyzer integration (conviction bucketing, coin stats, streak analysis)

Run these sequentially:

1. **Backtest Engine Tests**
   ```bash
   docker compose exec backend pytest tests/test_backtest_engine.py -v --tb=short
   ```
   Coverage: `test_long_win_outcome`, `test_short_loss_outcome`, `test_conviction_filter`, `test_compute_stats`

2. **Historical Outcome Resolution Tests**
   ```bash
   docker compose exec backend pytest tests/test_signal_log.py::TestHistoricalResolution -v --tb=short
   ```
   Coverage: `test_historical_long_tp_hit`, `test_historical_both_hit_bullish_candle`, `test_historical_review_no_candles`

3. **TradeAnalyzer Tests**
   ```bash
   docker compose exec backend pytest tests/test_analyzer.py -v --tb=short
   ```
   Coverage: `test_bucket_function`, `test_coin_stats_calculation`, `test_streak_analysis`, `test_compare_backtest_vs_live`

## Full Validation

Run all trading-engine tests:
```bash
docker compose exec backend pytest tests/test_backtest_engine.py tests/test_signal_log.py::TestHistoricalResolution tests/test_analyzer.py -v --tb=short
```

Covers silent-failure code paths in optimization and trading.

**Why:** Backtest engine bugs corrupt all sweep results. Historical resolution has complex candle-walk logic. TradeAnalyzer recommendations drive config changes.
