# Chart Provider Decoupling

## Problem

The navbar provider switcher calls `PUT /api/provider`, which sets Redis `config:provider` globally. The worker and orchestrator both read this key — so switching to OKX in the chart page to view a token like HYPE silently flips the paper trading engine to OKX prices until the user switches back.

## Fix: Per-page provider param (Option A)

Make the chart page provider selection local. Pass `?provider=okx` directly to OHLCV and Titan endpoints without calling `PUT /api/provider`. Global trading provider stays untouched.

The backend already supports this — `GET /api/strategy/titan/{symbol}?provider=okx` works without touching global config.

### Changes needed

| File | Change |
|------|--------|
| `frontend/src/app/chart/[symbol]/page.tsx` (or chart component) | Add local `provider` state, default to `"binance"` |
| Chart data fetching hooks | Pass provider as query param, not global state |
| Navbar provider switcher | Reserve for intentional trading provider changes only; remove from chart page or scope it |
| OHLCV endpoint | Verify it already accepts `?provider=` param |

### What to preserve

- Navbar global switcher still works for intentionally changing the trading provider
- Chart-local provider resets to `"binance"` on navigation (no persistent state needed)
- OKX-only tokens (HYPE, etc.) viewable without affecting paper trading

## Option B (simpler, less clean)

Keep global switcher but show a warning when switching with open positions:
> "You have N open Binance positions — switching provider may affect trade management."

## Recommended

Option A. Low risk, frontend-only change, backend already supports it.
