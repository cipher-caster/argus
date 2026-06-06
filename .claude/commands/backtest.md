# /backtest — Run Signal Backtest

**Usage:**
- `/backtest TAO` — backtest a single coin
- `/backtest TAO,LINK,AVAX` — backtest multiple coins
- `/backtest` — backtest default watchlist (BTC, ETH, BNB)

---

## How to Execute This Skill

The argument is: `$ARGUMENTS`

Parse `$ARGUMENTS`:
- If empty → use default coins (no `--symbols` flag)
- Otherwise → extract comma-separated coin tickers (e.g., `TAO` or `TAO,LINK`)

### Step 1: Check backend is running

Use `Bash` to run:
```
curl -sf http://localhost:8000/api/provider > /dev/null && echo "OK" || echo "OFFLINE"
```

If OFFLINE, tell the user to start the backend with `docker compose up -d`.

### Step 2: Run the backtest

Run via Docker with `--dry-run` and `--fix-optimal` flags (safe default — no DB writes, applies proven optimizations: BLOCK_SLEEPING + FIXED_TP_2.0x + SOFT_MACRO):

```bash
docker compose exec backend python scripts/run_signal_backtest.py --symbols={COINS} --dry-run --fix-optimal
```

Replace `{COINS}` with the parsed coin list (e.g., `TAO` or `TAO,LINK,AVAX`). If no coins specified, omit the `--symbols` flag entirely.

**Timeout:** Set a 120-second timeout — some backtests take a while for indicator computation.

### Step 3: Parse and present results

Read the script output. It prints:
1. Per-signal details (date, direction, entry, TP, SL, outcome)
2. An `OBSERVATIONS` section with stats

Present the results in this format:

```
## Backtest Results: {COINS} (4H, Optimized)

### Summary
- Total Signals: {N}
- Win Rate: {X}% ({W}W / {L}L / {R} Review)
- Total Profit: {X}R
- Avg Risk/Reward: {X}:1

### Per-Coin Breakdown
For each coin:
  **{COIN}**: {N} signals | {WR}% WR | {profit}R profit
  - Longs: {N} ({WR}% WR)
  - Shorts: {N} ({WR}% WR)
  - Best state: {state with highest WR}

### Signal Details
List each signal in a table:
| Date | Direction | Entry | TP | SL | Conviction | Outcome |

### Verdict
Based on the results, give a clear recommendation:
- **ADD TO WATCHLIST** — if win rate > 40% AND total profit > 0R AND >= 3 closed trades
- **MARGINAL** — if win rate 33-40% OR total profit near 0R OR < 3 closed trades
- **SKIP** — if win rate < 33% OR total profit negative
- **INSUFFICIENT DATA** — if fewer than 200 warmup candles available (script will say "no candle data")

If the coin shows promise, suggest: "Run `/backtest {COIN}` without --dry-run to save results, then add to signal log watchlist via Settings."
```

### Step 4: Offer next steps

After presenting results, offer:
1. "Save to DB? I can re-run without `--dry-run` to persist the backtest results."
2. "Add to live watchlist? I can update the signal log config to include {COIN}."
3. "Tweak parameters? Try different `--sl-mult`, `--tp-mult`, or `--min-conv` values."

---

## Error Handling

- If the script outputs "no candle data" for a coin, explain that historical candles need to be fetched first (visit the coin's chart page at `/chart/{COIN}-USDT` to trigger on-demand fetch, then retry).
- If Docker is not running, tell the user to start it.
- If the script fails with an import error, the backend container may need rebuilding.
