# Optimization Knowledge

Persistent memory for the `/optimize` loop. The command reads this file before running
parameter sweeps (to avoid re-testing dead ends) and appends new findings after each run.

## Format

Append one section per sweep, newest last:

```
## YYYY-MM-DD — <sweep_name> (run_id: <id>)

| param | value | metric | result |
|-------|-------|--------|--------|
| ...   | ...   | ...    | ...    |

Decision: <1–2 sentence conclusion — applied / rejected / inconclusive, and why>
```

## Findings

_No runs recorded yet._
