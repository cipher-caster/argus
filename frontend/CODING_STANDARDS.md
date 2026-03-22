# Argus Frontend — Coding Standards

> Enforced conventions for the Argus Next.js frontend.
> Updated: 2026-03-22

---

## 1. API Layer

- **Single source of truth for `API_URL`**: Defined once in `lib/apiClient.ts`.
- **Centralized fetch wrapper**: All HTTP calls use `apiFetch<T>()` from `lib/apiClient.ts`.
  - Handles error checking, JSON parsing, and typed returns in one place.
- **No inline `fetch()` calls** in components or hooks. Use API functions from `lib/`.

## 2. Types & Interfaces

- **One declaration per type.** If a type is shared across modules, export it from its canonical file and re-export where needed. Never re-declare.
- **Canonical locations:**
  - API response types → `lib/api.ts`, `lib/marketApi.ts`, `lib/indicatorApi.ts`
  - Store-internal state types → co-located in the store file
  - Shared indicator types → `lib/indicatorApi.ts` (import into store)

## 3. Data Fetching (React Query)

- All async data fetching **must** use React Query (`useQuery`, `useMutation`, `useInfiniteQuery`).
- **No manual `useState` + `useEffect` + `fetch`** patterns for server data.
- Hooks that fetch data must:
  - Have a descriptive, stable `queryKey` array.
  - Set `staleTime` appropriate to the data's volatility.
  - Use `placeholderData: keepPreviousData` when pagination or filter changes cause refetches.

## 4. Formatting Utilities

- All number/price/volume formatting lives in `lib/formatters.ts`.
- **Never re-implement** `formatPrice`, `formatVolume`, `formatChange`, etc. inline.
- Two price formatters available:
  - `formatPrice()` — dashboard display with dynamic precision (2/5/8 decimals)
  - `formatPriceCompact()` — table/compact display (2/4/6 decimals)

## 5. Error Handling

- API functions throw `new Error(...)` with descriptive messages.
- Components rely on React Query's `isError` / `error` states.
- **Never swallow errors silently** (empty `catch {}` blocks). At minimum, log to an error tracking service or rethrow.

## 6. File Naming

| Category | Convention | Example |
|----------|-----------|---------|
| Components | `PascalCase.tsx` | `BestSetups.tsx` |
| Hooks | `camelCase.ts` starting with `use` | `useMarketData.ts` |
| Utilities | `camelCase.ts` | `formatters.ts` |
| Stores | `camelCase.ts` ending with `Store` | `indicatorStore.ts` |

## 7. `'use client'` Directives

- **Every file** that uses React hooks (`useState`, `useEffect`, `useQuery`, `useRef`, etc.) must start with `"use client";`.
- Server components (no hooks, no interactivity) omit the directive.

## 8. Logging

- **No `console.log` or `console.warn`** in production code.
- Use structured logging or error boundaries for error reporting.
- `console.error` is acceptable only inside `catch` blocks for critical failures.

## 9. State Management

- **No module-level mutable variables** (`let x = 0` at file scope).
- Mutable state belongs in:
  - Zustand stores (for client-side global state)
  - React Query cache (for server state)
  - Component-local `useState` (for UI state)

## 10. Component Organization

- Components in `components/` must be organized by domain:
  - `components/analytics/` — analytics-specific components
  - `components/trading/` — trading-specific components
  - `components/common/` — shared layout components
  - `components/ui/` — primitive UI components
  - `components/features/` — feature-specific composites
- **No loose component files** at the root of `components/`.
