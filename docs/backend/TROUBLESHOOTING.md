# Troubleshooting Guide 🔍

This guide helps you resolve common issues encountered while developing or running Argus.

## 🛠️ Common Fixes

### 1. "422 Unprocessable Entity" Errors

- **Cause**: The Frontend sent a query parameter or body that the Backend FastAPI schema rejected.
- **Fix**: Check the **Network Tab** in your browser to see the exact payload. Compare it against the Backend regex patterns or Pydantic models in `backend/app/routes/*.py`.

### 2. Stale OHLCV Data

- **Cause**: The Backend is returning cached records from PostgreSQL that are outdated.
- **Fix**: We have implemented a staleness check. If the data still feels old, click the **Refresh** button in the Chart Header to force a fresh fetch from Binance.

### 3. Redis Connection Failures

- **Cause**: The API or Worker cannot connect to Redis (Port 6379).
- **Fix**: Ensure the Redis container is running:
  ```bash
  docker compose ps
  # If down:
  docker compose up -d redis
  ```

### 4. missing Coins/Logos in Table

- **Cause**: The Snapshot worker hasn't run yet or CoinGecko rate limits were hit.
- **Fix**: You can manually trigger a metadata sync:
  ```bash
  cd backend
  ./venv/bin/python3 scripts/sync_coins.py --limit 250
  ```

## 🔍 Investigation Tools

- **Backend Swagger Docs**: Visit `http://localhost:8000/docs`. This is the best way to test if the API is working independently of the React frontend.
- **Uvicorn Logs**: Check the terminal running the backend for detailed validation error messages.
- **Playwright Trace**: If E2E tests fail, use `npx playwright show-report` to see screenshots of the failure point.

## 🛟 Getting Help

If you encounter a new "gotcha," please document it here or in `docs/CONTEXT.md` to help the next developer!
