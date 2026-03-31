# Phase 21A — OKX Integration Completion Plan

## Status Summary

| Item | Status |
|------|--------|
| OKXProvider + okx_backtest.py | ✅ Done |
| BacktestPerformance provider toggle | ✅ Done |
| SignalLog provider filter | ✅ Done |
| Chart provider decoupling | ❌ Pending |
| `provider-comparison` API endpoint | ❌ Pending |
| `TRADING_PROVIDER` config (paper trading) | ❌ Pending |
| Daily OKX backfill cron job | ❌ Pending |

---

## Task 1 — Chart Provider Decoupling (frontend-only)

**Problem:** The navbar provider switcher calls `PUT /api/provider`, setting Redis `config:provider` globally. Switching to OKX on the chart page silently flips the paper trading engine to OKX prices.

**Fix (Option A):** Make chart page provider selection local — pass `?provider=okx` directly to OHLCV and Titan endpoints without touching global config. Backend already supports this (`GET /api/strategy/titan/{symbol}?provider=okx` works today).

**Changes:**

| File | Change |
|------|--------|
| `frontend/src/app/chart/[symbol]/page.tsx` | Add local `provider` state, default `"binance"` |
| Chart data hooks (`useOHLCV`, `useTitanSignal`, etc.) | Pass provider as query param, not global state |
| Navbar provider switcher | Scope to intentional trading provider changes only; remove from chart page or hide it there |

**Rules:**
- Chart-local provider resets to `"binance"` on navigation (no persistent state needed)
- OKX-only tokens (HYPE, etc.) viewable without affecting paper trading
- Global `PUT /api/provider` still exists for intentional trading provider changes

---

## Task 2 — `GET /api/analytics/provider-comparison` Endpoint

**Purpose:** Show signal win rate side-by-side for Binance vs OKX — answers "is OKX actually better for FET/ATOM?"

**Implementation:**

Add to `backend/app/routes/analytics.py`:

```
GET /api/analytics/provider-comparison
```

Query `SignalLog` grouped by `provider`, aggregate:
- `win_rate` (WIN / resolved count)
- `total_signals`, `wins`, `losses`
- `avg_r_profit` (mean R-multiple on closed signals)
- Per-coin breakdown (top movers for each provider)

Response shape:
```json
{
  "binance": { "win_rate": 0.51, "total": 320, "top_coins": [...] },
  "okx":     { "win_rate": 0.58, "total": 140, "top_coins": [...] }
}
```

Wire up frontend hook `useProviderComparison()` in `hooks/useAnalyticsData.ts` and surface it in `BacktestPerformance.tsx` as a summary row above the coin table.

---

## Task 3 — `TRADING_PROVIDER` Config (Paper Trading)

**Purpose:** Allow the orchestrator to route new signals to OKX instead of Binance without a code change.

**Changes:**

1. `backend/app/trading/orchestrator.py` — add to `DEFAULT_TRADING_CONFIG`:
   ```python
   "trading_provider": "binance"  # "binance" | "okx"
   ```
2. `backend/app/schemas/trading.py` — add `trading_provider: str` to `TradingConfig` / `TradingConfigUpdate` with validation (`binance` or `okx`).
3. Orchestrator `execute_signals()` — use `get_provider(config["trading_provider"])` instead of the global singleton when opening positions.
4. Frontend `TradingConfig` panel — add provider toggle (Binance / OKX) alongside existing config fields.

**Constraint:** Must not affect existing open positions — provider change only applies to new signals opened after the config update.

---

## Task 4 — Daily OKX Backfill Cron Job

**Purpose:** Keep OKX OHLCV data current so backtest stats and signal log stay fresh without manual runs.

**Implementation:**

Add to `backend/app/worker.py`:

```python
async def backfill_okx_candles(ctx):
    """Daily OKX candle backfill — last 7 days for watchlist symbols."""
    from app.scripts.backfill_history import run_backfill
    await run_backfill(provider="okx", days=7, symbols=WATCHLIST)
```

Register in `cron_jobs`:
```python
cron(backfill_okx_candles, hour={2}, minute={0})  # 02:00 UTC daily
```

Wrap in the existing worker retry helper. Log success/failure to activity log.

---

## Order of Implementation

1. **Task 1** (chart decoupling) — frontend-only, zero backend risk, unblocks OKX chart viewing
2. **Task 4** (backfill cron) — simple worker addition, keeps data fresh for everything else
3. **Task 2** (provider-comparison endpoint) — needs fresh OKX data to be meaningful
4. **Task 3** (TRADING_PROVIDER config) — last, after OKX data quality is validated via Task 2
