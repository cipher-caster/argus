---
name: argus-market-intelligence
description: Provides real-time cryptocurrency market analysis and signal reporting using the Argus platform. Use when the user asks for market summaries, coin deep-dives (BTC, SOL, etc.), backtesting strategies, portfolio management, or long-term investment (HODL) views.
---

# Argus Market Intelligence

## Overview

This skill transforms Gemini CLI into a specialized crypto market analyst and trade manager using the Argus analytics platform. It provides high-fidelity reporting, strategy backtesting, and portfolio intelligence.

## Core Workflows

### 1. Market Intelligence (`/read`)
Generate structured reports for the broad market or specific coins.
- **Trigger:** "How is the market?", "Report on BTC", "Analyze SOL".
- **Data Source:** `/api/market/summary`, `/api/analytics/signal-summary`, `/api/analytics/screener`, `/api/analytics/best-setups`, `/api/indicators/market/dashboard`.
- **Logic:**
  - For market reports, parallelize calls to all pulse endpoints.
  - For coin reports, resolve ticker to `BASE/USDT`, handle optional timeframes, and check for long-term (HODL) intent keywords.
- **Template:** See `references/report_templates.md#market-report` and `#coin-report`.

### 2. Strategy Backtesting (`/backtest`)
Validate Oracle and Titan strategies against historical candle data.
- **Trigger:** "Backtest TAO", "How does LINK perform?".
- **Action:** 
  1. Verify backend is alive.
  2. Run `docker compose exec backend python scripts/run_signal_backtest.py --symbols={COINS} --dry-run --fix-optimal`.
  3. Parse the `OBSERVATIONS` section and per-signal details.
- **Verdict:** Issue a clear recommendation: **ADD TO WATCHLIST** (WR > 40%, profit > 0R), **MARGINAL**, or **SKIP**.
- **Template:** See `references/report_templates.md#backtest-results`.

### 3. Portfolio & Trade Management (`/portfolio`, `/trade`)
Real-time tracking of paper trading positions and performance.
- **Trigger:** "Show my portfolio", "What are my open trades?", "Performance stats".
- **Data Source:** `/api/trading/portfolio`, `/api/trading/positions`, `/api/trading/stats`, `/api/trading/history`.
- **Intelligence:** Include "Trade Intelligence" (best/worst coins, market state win rates, conviction sweet spots) if >= 10 trades exist.
- **Template:** See `references/report_templates.md#portfolio-report`.

### 4. Trading Optimization (`/optimize`)
Improve system performance via parameter sweeps and learning loops.
- **Trigger:** "Optimize my trading", "Run an SL sweep".
- **Action:**
  1. Read `docs/trading/knowledge.md` to avoid redundant tests.
  2. Run `docker compose exec backend python scripts/optimize_trading.py --preset={sl_sweep|tp_sweep|confidence_sweep|gate_sweep|full_grid}`.
  3. Analyze results via `/api/optimization/experiments`.
  4. Apply best config and append findings to `docs/trading/knowledge.md`.

### 5. System Review (`/review`)
Audit the end-to-end signal pipeline and documentation health.
- **Trigger:** "Argus health check", "Review the system".
- **Action:** Check Signal Log flow (Scanner -> Live -> Resolved), Paper Trading state, Worker cron schedules (in `worker.py`), and Documentation freshness (CHANGELOG, ROADMAP, knowledge.md).

## Resource Guides

- **Interpretation:** See `references/interpretation_guide.md` for Oracle scores, Titan signals, and MTF confluence meanings.
- **Templates:** See `references/report_templates.md` for detailed output structures.

## Usage Constraints
- **API Base:** `http://localhost:8000`
- **Symbol Format:** `BASE/USDT` (URL encode as `BASE%2FUSDT`).
- **Safety:** Always use `--dry-run` for backtests unless persistence is explicitly requested.
- **Communication:** Amazon 4Cs (Clear, Concise, Consistent, Correct). No fluff.
