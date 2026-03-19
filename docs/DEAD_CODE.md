# Dead Code & Technical Debt

Last updated: 2026-03-19

## Oracle (Prophet v9.0) — Removed from UI, Code Preserved

Oracle is no longer used as a signal source in the UI. See `docs/CHANGELOG.md` v0.9.0 for the reasoning (negative EV on BTC/ETH).

### Still Used (Chart Page)

| Code | Location | Used By |
|------|----------|---------|
| `GET /api/strategy/oracle/{symbol}` | `backend/app/routes/strategy.py` | Frontend chart page sidebar (`CoinDetailsPanel`), analysis modal (`CoinAnalysisModal`), chart markers (`OracleMarkers`) |
| `OracleStrategy` class | `backend/app/strategies/oracle.py` | Strategy route, signal_log job (for screener pre-warming) |
| `useStrategyOracle` hook | `frontend/src/hooks/useStrategyOracle.ts` | Chart page components |

### Dead Code (Can Be Removed)

**Frontend:**

| File | Lines | Reason |
|------|-------|--------|
| `frontend/src/components/analytics/OracleScreener.tsx` | 160 | Not imported anywhere |
| `frontend/src/components/OracleSignalSummary.tsx` | 30 | Not imported anywhere |
| `frontend/src/components/MarketSentimentBar.tsx` | 166 | Only consumer is dead `OracleSignalSummary` |
| `frontend/src/hooks/useAnalyticsData.ts` | hooks:33-42,56-65 | `useOracleScreener`, `useOracleSignalSummary` — unused |
| `frontend/src/lib/api.ts` | fn:198-201,216-219 | `fetchOracleScreener`, `fetchOracleSignalSummary` — unused |
| `frontend/src/lib/api.ts` | types:119-161 | `ScreenerItem`, `ScreenerResponse`, `OracleSignalSummaryResponse` — unused |

**Backend:**

| File | Lines | Reason |
|------|-------|--------|
| `backend/app/routes/analytics.py` | `get_oracle_screener` (91-114) | No frontend calls this endpoint |
| `backend/app/routes/analytics.py` | `get_oracle_signal_summary` (143-174) | No frontend calls this endpoint |
| `backend/app/worker.py` | screener/signal-summary cache warming (427-458) | Calls dead endpoints, wasted compute |

### Tests That Reference Dead Code

| File | Test | Status |
|------|------|--------|
| `tests/test_screener_robustness.py` | Tests Oracle screener NaN handling | Can keep (screener code still exists) |
| `tests/test_analytics_new.py` | Tests `/api/analytics/screener` and `/signal-summary` | Still pass but test dead routes |

### Stale Analysis Scripts

One-off scripts from the BTC/ETH analysis. Not part of the core system.

| Script | Purpose | Superseded By |
|--------|---------|---------------|
| `scripts/btc_timeframe_analysis.py` | Multi-timeframe comparison | `run_signal_backtest.py` |
| `scripts/btc_titan_deep_dive.py` | Extended backtest + sweep | `optimize_trading.py` |
| `scripts/btc_4h_sweep.py` | 4H parameter sweep | `optimize_trading.py --preset=sl_sweep` |
| `scripts/btc_hodl_vs_trade.py` | HODL vs trading comparison | One-off analysis |
| `scripts/btc_eth_db_verify.py` | DB-verified backtest | One-off analysis |
| `scripts/eth_full_analysis.py` | ETH multi-timeframe | One-off analysis |
| `scripts/backtest_strategy.py` | Early prototype backtest | `run_signal_backtest.py` |

### Stale Verify Scripts

| Script | Reason |
|--------|--------|
| `tests/verify_refactor.py` | Manual smoke test, not automated |
| `tests/verify_freshness.py` | Manual smoke test, not automated |

## Removed Components (No Backtest Proof)

| Component | File | Why Removed |
|-----------|------|-------------|
| **ContrarianRadar** | `frontend/src/components/analytics/ContrarianRadar.tsx` | No backtest data. Mean reversion opposite of trend following. Zero evidence of profitability. |
| `useContrarianRadar` hook | `frontend/src/hooks/useAnalyticsData.ts` | Only consumer was ContrarianRadar |
| `fetchMeanReversion` API fn | `frontend/src/lib/api.ts` | Only consumer was useContrarianRadar |
| `detect_mean_reversion` | `backend/app/indicators/mean_reversion.py` | Only used by dead contrarian-radar endpoint |
| `GET /api/analytics/contrarian-radar` | `backend/app/routes/analytics.py` | No frontend calls after removal |

## Naming Inconsistencies (Fixed)

- ~~Dashboard: "Active Setups" vs Analytics: "Best Setups"~~ → Both now say "Best Setups"
- ~~"Oracle Signal" header on chart sidebar~~ → Now "Analysis"
