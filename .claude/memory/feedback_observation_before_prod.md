---
name: Observation Period Before Production
description: User requires a hands-off observation period with paper trading profitability proof before deploying to production
type: feedback
---

Always include an observation/validation period after implementing trading system changes before going to production. Don't just ship fixes — prove they work with real paper trading data first.

**Why:** User's philosophy is data-driven. Theoretical edge (backtest) is not enough — must demonstrate profitability in live paper trading with reset capital before going live.

**How to apply:** After any trading engine changes, propose an observation period with clear success criteria (WR, profitability, drawdown limits) before recommending production deployment.
