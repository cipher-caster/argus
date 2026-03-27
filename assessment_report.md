# Argus Backend — Deep Codebase Assessment

> **Scope**: Full code review of ~5,500 LOC across 25+ source files in `backend/app/`.
> **Test suite**: 27 test files + `conftest.py` in `backend/tests/`.

---

## ✅ What You're Doing Right

| Area | Evidence |
|------|----------|
| **Clean Architecture** | Proper separation: `routes/` → `services/` → `providers/` → `storage.py`. Provider abstraction (`DataProvider` ABC) enables clean Binance/OKX swap. |
| **Strategy Engines** | Oracle (442 LOC) and Titan (404 LOC) are well-structured with clear scoring logic, SMC integration (FVG/MSS/Sweep), and per-symbol risk overrides. |
| **Risk Management** | 8-gate risk pipeline in `RiskManager.check_all()`: drawdown → positions → correlation → conviction → volatility → sizing → min order → exposure. Solid. |
| **Worker Recovery** | Impressive: heartbeat gap detection → missed 4H candle close recovery → historical signal resolution with 5-min tiebreaker. Most projects skip this entirely. |
| **Error Handling** | Custom exception hierarchy (`ArgusException` → `DataProviderError`, `CacheError`, etc.). Routes consistently map exceptions to proper HTTP status codes. |
| **Test Infrastructure** | `conftest.py` has proper shared fixtures (`make_ohlcv`, `make_bullish_ohlcv`, mock cache helpers). 27 test files covering analytics, strategies, trading, signal log, and edge cases. |
| **Provider Fallback** | Worker probes non-Binance providers with 4s timeout and auto-falls back to Binance with 5-min backoff. Smart resilience. |
| **Trade Orchestrator** | Full lifecycle: `process_signal()` → `check_pending_fills()` → `check_open_positions()` → circuit breaker. |

---

## ⚠️ Issues Found (by severity)

### 🔴 Critical

#### 1. Provider Leak — New Provider Created on Every OHLCV Request

```python
# services/market_data.py:103
provider = get_provider()  # Creates NEW BinanceProvider each time
try:
    fresh_candles = await provider.get_ohlcv(...)
finally:
    await provider.close()
```

**Problem**: `get_provider()` instantiates a *new* CCXT exchange client every call. Each instance calls `load_markets()` (~1 API call). Under load, this hammers Binance's API and creates orphan connections.

**Same pattern in**: `routes/analytics.py:59` (`fetch_all_candles`), `routes/strategy.py:77`, `services/market_data.py:350`.

**Fix**: Inject a shared provider via `lifespan` or use `get_active_provider()` from `worker.py` as the canonical pattern.

---

#### 2. Hardcoded `provider="binance"` When Saving Candles

```python
# services/market_data.py:118, routes/strategy.py:89
candle_db = DbCandle(
    ...
    provider="binance",  # ← hardcoded even when using OKX
)
```

**Problem**: If you switch to OKX via `/api/provider`, fetched candles are still saved with `provider="binance"`. The DB query filters by `active_provider`, so next time it reads OKX candles — it finds nothing, fetches again, saves with wrong tag. Infinite miss loop.

**Fix**: Use `provider.name` or the resolved active provider name.

---

#### 3. Tiebreaker Uses Closed Provider

```python
# jobs/signal_log.py:491
tiebreak = await _resolve_tiebreaker_5m(
    sig.symbol, sig.direction, sig.tp, sig.sl,
    c_time, shared_provider,  # ← already closed in finally block above
)
```

**Problem**: `shared_provider.close()` is called in the `finally` block (line 434), but the tiebreaker is invoked *after* that inside the same loop. The provider is already closed. This will silently fail and always default to LOSS (conservative fallback).

---

### 🟡 Moderate

#### 4. Dual Provider State (Backend vs Worker)

The backend API and worker maintain **independent** provider state:

| Component | Provider Source |
|-----------|---------------|
| `main.py` | `_provider` global, set in `lifespan` |
| `worker.py` | `_active_provider` global, tracks Redis `config:provider` |
| `routes/strategy.py` | `get_provider()` factory (reads `DATA_PROVIDER` env-var) |
| `services/market_data.py` | `get_provider()` factory (reads `DATA_PROVIDER` env-var) |

**Problem**: Switching provider via `/api/provider` updates `main.py` global + Redis + env-var, but `get_provider()` factory used by `strategy.py` and `market_data.py` only reads the env-var. In Docker, the worker process has its own env — it won't see `os.environ` changes from the backend process.

---

#### 5. `_passes_market_gate()` Always Returns True

```python
# jobs/signal_log.py:149-158
def _passes_market_gate(regime: str, config: dict) -> bool:
    if regime == "UNKNOWN":
        return True
    if config.get("bear_long_only", False) and regime == "BEAR":
        return True
    return True  # ← Always True. Dead code.
```

The function is defined but every branch returns `True`. It's never actually used in the code either. This looks like leftover from a refactor.

---

#### 6. Oracle Backtest Doesn't Handle Timestamp Types

```python
# strategies/oracle.py:119
active_trade['exit_time'] = int(row['timestamp'].timestamp() * 1000)
```

When `df_micro['timestamp']` contains raw integer timestamps (from API) vs `pd.Timestamp` objects (from DB), calling `.timestamp()` on an int raises `AttributeError`. This is inconsistent with how `calculator.py` handles the same issue:

```python
# calculator.py:366 — correct pattern
int(ts.timestamp() * 1000) if isinstance(ts, pd.Timestamp) else int(ts)
```

---

#### 7. No `close()` on `DataProvider` ABC

```python
# providers/data_provider.py — DataProvider ABC
# Missing: close(), get_all_tickers()
```

`close()` and `get_all_tickers()` are used everywhere but aren't in the abstract base class. Subclasses implement them, but there's no contract enforcement.

---

### 🟢 Minor / Cleanup

| Issue | Location | Note |
|-------|----------|------|
| **Duplicate docstring** | `oracle.py:30-31` | `:param df_micro` and `:param df_macro` appear twice |
| **Unused imports** | `tests/test_fvg_detection.py` | `importlib.metadata`, `os` |
| **`sys.path.append("/app")`** | `tests/test_fvg_detection.py` etc. | Brittle Docker-only path hack |
| **Duplicate test location** | `backend/test_fvg.py` + `tests/test_fvg_detection.py` | Same tests in two places |
| **Magic numbers** | `market_data.py:200` | `15.5` multiplier for fake market cap — could use a named constant |
| **Swallowed exception** | `market_data.py:373` | `except Exception: pass` — hides provider errors silently |
| **Manual serialization** | `trading.py:59` `_serialize_position()` | Could use Pydantic `model_dump()` |
| **TODO left in code** | `titan.py:216` | `# TODO: Implement historical percentile check` |

---

## 📊 Summary Matrix

| Category | Grade | Notes |
|----------|-------|-------|
| Architecture | **A** | Clean separation, good abstractions |
| Strategy Logic | **A** | Oracle + Titan are thorough and well-documented |
| Risk Management | **A** | Comprehensive 8-gate pipeline |
| Worker / Jobs | **A-** | Strong recovery logic, but tiebreaker bug (🔴 #3) |
| Provider Management | **C** | Provider leak (🔴 #1), hardcoded tag (🔴 #2), split state (🟡 #4) |
| Test Coverage | **B+** | 27 test files, good fixtures, but root `tests/` has stale scripts |
| Error Handling | **B+** | Good exception hierarchy, some silent swallows |

---

## Recommended Operation Path

**Phase 1** — Fix the 3 critical bugs (🔴):
1. Shared provider singleton for OHLCV/strategy fetches
2. Dynamic `provider` tag when persisting candles
3. Fix closed-provider tiebreaker in signal resolution

**Phase 2** — Reconcile provider state (🟡 #4):
- Single source of truth for active provider (Redis `config:provider`)
- Remove `os.environ` mutations

**Phase 3** — Cleanup (🟢):
- Remove dead code (`_passes_market_gate`)
- Add `close()` and `get_all_tickers()` to `DataProvider` ABC
- Remove duplicate test files, fix `sys.path` hacks
