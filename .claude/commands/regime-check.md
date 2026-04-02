Call the Argus backend and produce a regime alignment diagnostic.

Make these API calls (backend at http://localhost:8000):
1. GET /api/strategy/regime
2. GET /api/trading/history?limit=5
3. GET /api/trading/positions?status=PENDING

If the backend is down, say so and suggest `docker-compose up -d`.

Then run this SQL via `docker compose exec db psql -U argus -c "<query>"`:

```sql
SELECT outcome, COUNT(*) as cnt, ROUND(AVG(pnl_pct)::numeric, 2) as avg_pnl
FROM positions
WHERE status = 'CLOSED'
  AND closed_at > EXTRACT(EPOCH FROM NOW() - INTERVAL '7 days') * 1000
GROUP BY outcome;
```

Format the output as:

---

## Argus Regime Check — {today's date}

### Current Regime
- **Weekly EMA50:** {BULL/BEAR/UNKNOWN}
- **Regime cached:** {from regime endpoint}

### 7-Day Performance
- Wins: {count} (avg {pnl}%) | Losses: {count} (avg {pnl}%)
- Net: {total_pnl}

### Timeframe Alignment Check
Look at the last 5 closed trades:
- If 3+ consecutive losses in same direction → flag as **REGIME LAG DETECTED**
- If all pending orders are same direction as recent losses → flag as **REPEAT EXPOSURE**
- If wins and losses are mixed → **ALIGNED** (regime filter working)

### Diagnosis
Based on the data:
- If regime lag detected: recommend pausing trading or closing pending orders
- If repeat exposure: warn that pending orders may face same headwind
- If aligned: system is operating normally

### Recommended Actions
- If problematic: suggest `POST /api/trading/pause` and review
- If healthy: no action needed

---

**Context:** This skill monitors for the regime lag problem where weekly EMA50 stays BEAR/BULL while shorter timeframes have reversed. Option D (multi-timeframe confirmation requiring 4H EMA200 + weekly EMA50 agreement) is the planned permanent fix. Until then, use this skill to catch the problem early.
