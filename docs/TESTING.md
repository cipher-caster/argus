# Testing Guide

This document outlines the testing strategy and execution steps for the Argus application.

## Overview

We use a layered testing approach:

1. **Backend Unit Tests**: Verify business logic, data staleness checks, and mathematics (e.g. liquidation aggregation).
2. **Frontend E2E Tests**: Verify user flows, page navigation, and critical UI elements using Playwright.

---

## Backend Testing

**Framework**: `pytest`, `pytest-asyncio`, `pytest-mock`

### Key Test Files

| File                        | Purpose                                                                                                        |
| --------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `tests/conftest.py`         | Fixtures for AsyncClient and DB session mocking.                                                               |
| `tests/test_market.py`      | Verifies `get_ohlcv` logic. Specifically ensures that finding stale DB data triggers a fresh Binance fetch.    |
| `tests/test_liquidation.py` | Verifies `LiquidationAggregator`. Ensures raw WebSocket events are correctly bucketed by time (15s) and price. |

### Running Tests

**Option 1: Inside Docker (Recommended)**
Ensures the environment matches production.

```bash
docker compose exec backend sh -c "export PYTHONPATH=$PYTHONPATH:/app && pytest"
```

**Option 2: Local Venv**
Requires `pip install -r requirements.txt`.

```bash
export PYTHONPATH=$PYTHONPATH:.
pytest
```

---

## Frontend Testing

**Framework**: Playwright

### Key Test Files

| File                | Purpose                                                                                                |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| `tests/e2e.spec.ts` | Complete regression suite. Covers Homepage, Chart/Analytics/Liquidation navigation, and feature flags. |

### Running Tests

1. Start the development server:

   ```bash
   npm run dev
   ```

2. Run Playwright:

   ```bash
   npx playwright test
   ```

3. View Report (on failure):
   ```bash
   npx playwright show-report
   ```

### Debugging Selectors

If tests fail due to "element not found", check `e2e.spec.ts`. We use strict selectors:

- **Good**: `page.getByRole('button', { name: 'Funding Rate' })`
- **Good**: `page.locator('a[href^="/chart/"]').first()`
- **Avoid**: Generic text matchers like `getByText("Argus")` if multiple elements exist.

---

## CI/CD Integration

(Proposed)

- **On PR**: Run `pytest` and `npx playwright test`.
- **On Merge**: Deploy to staging.
