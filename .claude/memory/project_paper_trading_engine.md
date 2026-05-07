---
name: Paper Trading Engine
description: Paper trading engine architecture, signal sources, current config, and relationship to signal log
type: project
originSessionId: e8dc91a7-8713-485f-bd3f-8e7acb71133b
---
Argus paper trading engine simulates Titan signals against real market prices (v0.8.0+).

## Architecture
- `backend/app/schemas/trading.py` — `Position` and `TradeEvent` SQLModel tables
- `backend/app/trading/risk_manager.py` — gates: drawdown, max positions, correlation, conviction, min order size
- `backend/app/trading/portfolio.py` — balance, unrealized PnL, exposure, stats, equity curve
- `backend/app/trading/orchestrator.py` — simulation engine (PENDING→OPEN→CLOSED lifecycle)
- `backend/app/trading/notifier.py` — optional Telegram alerts
- `backend/app/routes/trading.py` — REST API at `/api/trading/...`
- Worker jobs: `execute_signals` (every 10 min), `manage_positions` (every 5 min), `sync_trading_balance` (every 10 min)

## Signal Sources Fed Into Paper Trading
- `live` — 4H candle close, **watchlist only**, 6x/day
- `scanner` — best-setups cache, **top-50 logged but only watchlist traded**, every 5 min
- `counter` — NOT traded, observation/scouting only

`execute_signals` applies a watchlist filter before passing signals to the orchestrator. Non-watchlist scanner signals are tracked in Signal Log but never create positions.

## Current Config (DEFAULT_TRADING_CONFIG in orchestrator.py, as of v1.1.4)
- `enabled`: False
- `initial_capital`: $1000.0
- `max_position_size_pct`: 3.0% per trade
- `max_concurrent_positions`: 3
- `max_correlated_positions`: 2
- `max_drawdown_pct`: 15.0%
- `max_leverage`: 2.0
- `min_conviction`: 56
- `max_total_exposure_pct`: 200.0%
- `order_expiry_hours`: 16
- `trading_provider`: "okx"
- `correlation_groups`: btc_correlated = [BTCUSDT, ETHUSDT, BNBUSDT, ARBUSDT, NEARUSDT]

Note: DEFAULT_TRADING_CONFIG in `orchestrator.py` is the fallback. Live config is persisted in Redis key `trading:config` and takes precedence. To apply default changes to a running system, update via the `/api/trading/config` endpoint or flush Redis.

## Optimization System
- `backend/app/trading/backtest_engine.py` — reusable backtest core
- `backend/app/trading/analyzer.py` — TradeAnalyzer: backtest vs live comparison, recommendations
- `backend/scripts/optimize_trading.py` — CLI with 5 presets (sl_sweep, tp_sweep, confidence_sweep, gate_sweep, full_grid)
- `backend/app/routes/optimization.py` — API: experiments, best, apply, analysis
- `docs/trading/knowledge.md` — confirmed findings and dead ends

**Slash commands:** `/portfolio`, `/trade`, `/optimize`

**Why:** Paper trade to gather real forward-test data before going live. Watchlist filter ensures only backtested coins are traded.
**How to apply:** Open positions will always be watchlist coins. Config changes to DEFAULT_TRADING_CONFIG require Redis flush or API update to take effect on a running instance.
