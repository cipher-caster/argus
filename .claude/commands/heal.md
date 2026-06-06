# /heal — Self-Healing Backend Monitor

Diagnose and repair a broken Argus backend by tracing the data flow from the
symptom back to its root cause, proving the cause with a command, fixing it,
and proving the fix with the same command.

**Usage:**
- `/heal` — auto-triage: detect the symptom, then diagnose → verify → fix → prove
- `/heal <symptom>` — start from a known symptom, e.g. `/heal empty dashboard`,
  `/heal missing market data`, `/heal cron not firing`, `/heal signals stuck OPEN`

---

## Operating rules (non-negotiable)

1. **Root cause, not symptom.** Read logs and trace data flow step-by-step down
   the layers below. Name the single layer that first breaks. Do not patch a
   downstream symptom.
2. **Prove external endpoints.** Before claiming any external URL/host is the
   "official" or "correct" endpoint, actually resolve and `curl` it and show the
   response. Never assert an endpoint is official from memory. (Argus's external
   deps: CoinGecko for snapshots, OKX + Binance via CCXT.)
3. **Verify before and after.** Before any fix, run one command that *confirms*
   the root cause (the "red" check). Apply the fix. Re-run the *same* command to
   prove it's now "green". A fix without a before/after diff is not done.
4. **Be concise.** Run the minimum commands needed to localize the break. Stop
   probing a layer once it's confirmed healthy. No exhaustive sweeps.
5. **Commit only verified fixes.** Code/file fixes that passed the after-check →
   commit and push. **Risky config changes** (trading params, risk %, conviction,
   watchlist, provider/API keys, cron timing, anything in the closed-experiment
   memories) → STOP and ask the user first. Never auto-commit those.

---

## The data flow (trace top-down; the first broken layer is the root cause)

```
External APIs        OKX / Binance (CCXT) · CoinGecko          ← step 2: curl to prove
   │ worker fetch
Worker (arq cron)    sync_*, log_*, resolve_*, execute_*       ← cron blocked / job erroring
   │ writes
Postgres + Redis     positions, signals · cache (30–180s TTL)  ← stale / empty store
   │ read
Backend (FastAPI)    /health, routes/*, services/market_data   ← 503 / degraded / cache miss
   │ HTTP
Frontend (Next.js)   pages, TanStack Query hooks               ← empty dashboard (downstream)
```

Symptom → most likely layer:
- **Empty dashboard / blank widgets** → usually NOT the frontend. Walk up: backend
  reachable? `/health` healthy? cache populated? worker writing it?
- **Missing / stale market data** → worker `sync_market_summary` (60s) or
  `sync_market_snapshot` (CoinGecko, 5m) failing, or its external source down.
- **Cron not firing / blocked** → worker container down, Redis (arq broker) down,
  or a job raising before scheduling. Check worker logs for tracebacks + last run.
- **Signals stuck OPEN / no trades** → `execute_signals` / `manage_positions` /
  `resolve_signal_outcomes` jobs (this is pipeline logic, defer to `/review trading`).

---

## Step 1 — Localize (minimum probes)

Run only as far down as needed to find the first red layer.

```bash
# Services up?
docker compose ps
# Backend + dependency health (returns degraded/503 with per-dep checks)
curl -s http://localhost:8000/health | jq .
# Frontend reachable?
curl -s -o /dev/null -w "frontend: %{http_code}\n" http://localhost:3000
```

If nothing is running: `docker-compose up -d` (NOT `--build` — build separately
if code changed, per project convention), wait ~15s, re-probe.

Then read logs **only for the suspect layer**, newest first:
```bash
docker compose logs --tail=80 backend     # 503s, tracebacks, cache errors
docker compose logs --tail=80 worker      # job tracebacks, "cron" gaps, fetch failures
docker compose logs --tail=40 redis db    # connection refused, OOM, disk full
```

Identify the **first** layer that breaks. That is the root cause candidate.

## Step 2 — Prove the root cause (the "red" check)

Write down one command whose output *demonstrates* the cause. Examples by layer:

- **External API suspected** — resolve and curl it; show the proof. Do NOT trust a
  URL from memory:
  ```bash
  getent hosts api.coingecko.com            # or the host CCXT actually targets
  curl -sS -o /dev/null -w "%{http_code} %{url_effective}\n" "<the-actual-url>"
  ```
  Confirm the host/path the code uses (grep `backend/app/providers/` or the
  snapshot job) — verify *that* endpoint, not one you assumed is official.
- **Worker cron blocked** — show the job is not running / erroring:
  ```bash
  docker compose logs --since=30m worker | grep -iE "error|traceback|<job_name>"
  docker compose exec redis redis-cli KEYS 'arq:*' | head
  ```
- **Cache empty / store stale** — show the missing/old key or empty table:
  ```bash
  docker compose exec redis redis-cli GET <cache_key>          # nil = empty
  docker compose exec db psql -U argus -c "SELECT count(*), max(created_at) FROM <table>;"
  ```
- **Backend degraded** — the `/health` JSON already names the failing dependency.

State plainly: *"Root cause: <layer> — <command> shows <red result>."*

## Step 3 — Fix

- Apply the **minimal** change at the root-cause layer.
- Code/file fix → edit it.
- Restart only what's needed: `docker compose restart <service>`.
- **Risky config change** (see rule 5) → do NOT apply. Present the proposed change
  + evidence to the user and wait for approval.

## Step 4 — Prove the fix (the "green" check)

Re-run the **exact same command** from Step 2. Show before vs after side by side.
If it's not green, the root cause was wrong — go back to Step 1, don't pile on
more fixes.

Optionally confirm end-to-end recovery:
```bash
curl -s http://localhost:8000/health | jq .status   # → "healthy"
```

## Step 5 — Commit (verified fixes only)

If the after-check is green AND the fix was code/files (not risky config):
```bash
git add -A && git commit -m "fix(heal): <root cause> — verified via <check>" && git push
```
Commit message must name the root cause and the verification command. End the
commit body with the standard Co-Authored-By line.

If the fix was risky config: leave it uncommitted, summarize for the user, stop.

---

## Output format

```
## /heal — {date}

**Symptom:** {what was reported / detected}
**Root cause:** {layer} — {one sentence}

**Proof (before):**
$ {verify command}
{red output}

**Fix:** {what changed, which file/service}

**Proof (after):**
$ {same verify command}
{green output}

**Action:** {committed <sha> & pushed | AWAITING APPROVAL — risky config: <what>}
```

Keep it tight. One root cause, one verification, one fix per run.
```
