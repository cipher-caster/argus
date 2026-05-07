---
name: Scanner v1 Small-Sample Bias
description: Never add a coin to the watchlist based on scanner WR alone — always run the full walkforward backtest first
type: feedback
originSessionId: afc794a0-6c3d-4aa4-a187-431834d04e87
---
Never add a coin to the watchlist based on scanner v1 WR alone. Always run the full walkforward backtest before making a watchlist decision.

**Why:** Scanner v1 fires opportunistically on small samples and inflates apparent WR. Apr 25 audit exposed this clearly:
- SOL: 87.5% scanner WR (16 signals) → 41.2% full backtest (34 signals), −1.3R
- LINK: 77.8% scanner WR (9 signals) → 38.7% full backtest (31 signals), −3.0R
- TON: 60.0% scanner WR (5 signals) → 16.7% full backtest (12 signals), −7.3R

**How to apply:** When evaluating a new coin candidate, scanner WR is a shortlist signal only. Run `/backtest` on the candidate with `--fix-optimal` walkforward before adding. Minimum ~30 signals for confidence; flag anything under 20 as provisional (like AAVE at 10 signals).
