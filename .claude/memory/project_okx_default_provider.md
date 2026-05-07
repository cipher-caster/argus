---
name: OKX is Default Trading Provider
description: OKX replaced Binance as the default (and only) trading provider. Binance fallback has been removed.
type: project
originSessionId: e8dc91a7-8713-485f-bd3f-8e7acb71133b
---
OKX is the **current default and sole trading provider** for Argus paper trading. This is not a planned feature — it shipped and is live.

**What changed (commits 87fa603, fe45702, 57070be):**
- `DEFAULT_TRADING_CONFIG["trading_provider"]` = `"okx"` (in `backend/app/trading/orchestrator.py`)
- Frontend provider default also switched to OKX (`fe45702`)
- Binance fallback removed and provider factory consolidated — no dual-provider logic remains (`57070be`)

**Implications for agents working on provider logic:**
- The `OKXProvider` class is the only active provider at runtime.
- There is no Binance fallback. If OKX fails, trading fails — there is no automatic switchover.
- `trading_provider` in `trading:config` Redis key overrides the default at runtime. Changing it via `/api/trading/config` is the only way to switch providers without a deploy.
- Historical candle data in Postgres is tagged by `provider` column — OKX data and any legacy Binance data coexist in the DB but live signals use OKX exclusively.
- `backend/app/providers/binance_provider.py` still exists for market data / screener use — it is NOT the trading provider.

**Backtest data:** The OKX_BACKTEST_REPORT (8.3 months, 19 coins) informed the watchlist. Top performers: ETH (68% WR), FET (61% WR), ATOM (58% WR). Exchange-specific: FET and ATOM were Binance losers but OKX winners.

**Why:** OKX showed better signal fill rates and backtest results than Binance for the current watchlist. The decision to make it default was final — do not propose reverting to Binance without new evidence.
**How to apply:** When touching orchestrator, provider factory, or trading config — treat OKX as the only provider. Do not reintroduce Binance as a fallback. If adding provider logic, use the existing `OKXProvider` interface.
