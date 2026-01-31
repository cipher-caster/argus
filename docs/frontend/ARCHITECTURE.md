# Frontend Architecture

**Last Updated**: 2026-01-31

---

## Overview

The Argus frontend is a **Next.js 14 application** using the App Router, TypeScript, and TanStack Query for server state management. It provides real-time cryptocurrency analytics through a responsive, interactive dashboard.

---

## Tech Stack

**Core**:

- **Next.js 14** - React framework with App Router
- **React 18** - UI library
- **TypeScript** - Type safety
- **TanStack Query** (React Query) - Server state management
- **Tailwind CSS** - Utility-first styling

**UI Components**:

- **Shadcn/ui** - Headless component library
- **Radix UI** - Accessible primitives
- **Lucide Icons** - Icon library

**Charts & Visualization**:

- **Lightweight Charts** - TradingView-style candlestick charts
- Custom components for analytics visualization

---

## Directory Structure

```
frontend/src/
├── app/                    # Next.js 14 App Router
│   ├── page.tsx           # Dashboard home
│   ├── analytics/         # Analytics pages
│   │   └── page.tsx       # Oracle Screener, Titan Radar, etc.
│   ├── chart/             # Chart viewer
│   │   └── [symbol]/      # Dynamic routes (BTC-USDT)
│   └── layout.tsx         # Root layout
├── components/            # React components
│   ├── analytics/         # Analytics-specific components
│   │   ├── OracleScreener.tsx
│   │   ├── MarketHealth.tsx
│   │   ├── TitanRadar.tsx
│   │   └── ...
│   ├── features/          # Feature-specific components
│   │   └── dashboard/     # Dashboard components
│   │       ├── CoinTable.tsx
│   │       ├── MarketIndicators.tsx
│   │       └── TopCoinsWidgets.tsx
│   └── ui/                # Reusable UI components (Shadcn)
│       ├── button.tsx
│       ├── skeleton.tsx
│       └── ...
├── hooks/                 # Custom React hooks
│   ├── useMarketData.ts   # OHLCV, tickers, symbols
│   ├── useAnalyticsData.ts # Analytics queries
│   ├── useMarketOverview.ts # Market summary
│   └── useCoinMeta.ts     # Coin metadata
├── lib/                   # Utilities and clients
│   ├── api.ts             # API client (fetch wrappers)
│   └── utils.ts           # Helper functions
└── public/                # Static assets
    └── data/coins/        # Coin metadata JSON
```

---

## Data Flow

### Server State Management with TanStack Query

```
Component
    ↓
Custom Hook (useSomething)
    ↓
TanStack Query (useQuery / useInfiniteQuery)
    ↓
API Client (lib/api.ts)
    ↓
Backend API
    ↓
Cache (automatic, configurable TTL)
    ↓
Re-render on data change
```

**Key Benefits**:

- **Automatic caching** - No manual cache management
- **Background refetching** - Keeps data fresh
- **Loading/error states** - Automatically managed
- **Deduplication** - Multiple components using same query share cache

### Example

```typescript
// Hook definition
export function useOracleScreener(timeframe: string = "1h", limit: number = 50) {
  return useQuery({
    queryKey: ["analytics", "screener", timeframe, limit],
    queryFn: () => fetchOracleScreener(timeframe, limit),
    staleTime: 120_000, // 2 minutes before considered stale
    gcTime: 5 * 60_000, // Keep in cache for 5 minutes
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData, // Smooth transitions
  });
}

// Component usage
function OracleScreener({ timeframe }: Props) {
  const { data, isLoading, error } = useOracleScreener(timeframe);

  if (isLoading) return <Skeleton />;
  if (error) return <Error />;

  return <Table data={data} />;
}
```

---

## Component Patterns

### Standard Component Structure

```typescript
"use client"; // Required for client components

import { useState } from "react";
import { useSomeData } from "@/hooks/useSomeData";

interface ComponentProps {
  prop1: string;
  prop2?: number;
}

export function Component({ prop1, prop2 = 100 }: ComponentProps) {
  // 1. Data fetching
  const { data, isLoading, error } = useSomeData(prop1);

  // 2. Local state
  const [filter, setFilter] = useState("");

  // 3. Derived state
  const filteredData = data?.filter(item => item.name.includes(filter));

  // 4. Event handlers
  const handleFilterChange = (value: string) => {
    setFilter(value);
  };

  // 5. Early returns (loading, error states)
  if (isLoading) return <Skeleton />;
  if (error) return <ErrorDisplay error={error} />;

  // 6. Main render
  return (
    <div className="space-y-4">
      <input value={filter} onChange={(e) => handleFilterChange(e.target.value)} />
      <div>{filteredData?.map(item => <Item key={item.id} data={item} />)}</div>
    </div>
  );
}
```

### Loading States

**Skeleton Pattern** (Preferred):

```typescript
if (isLoading) {
  return (
    <div className="space-y-4">
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="animate-pulse">
          <div className="w-full h-12 bg-muted rounded" />
        </div>
      ))}
    </div>
  );
}
```

**Benefits**:

- Shows layout immediately
- Better perceived performance
- Professional appearance

### Error States

```typescript
if (error) {
  return (
    <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-6">
      <p className="text-red-500 font-semibold">Failed to load data</p>
      <p className="text-sm text-muted-foreground">{error.message}</p>
    </div>
  );
}
```

---

## Performance Optimizations

### 1. Lazy Loading (Code Splitting)

**Heavy components** are lazily loaded using Next.js `dynamic()`:

```typescript
import dynamic from "next/dynamic";

const OracleScreener = dynamic(
  () => import("@/components/analytics").then((mod) => ({ default: mod.OracleScreener })),
  {
    loading: () => <div>Loading Oracle Screener...</div>,
  }
);
```

**Benefits**:

- **Smaller initial bundle** - Only loads code when needed
- **Faster page load** - Critical path is smaller
- **Better user experience** - Progressive enhancement

**Currently Lazy Loaded**:

- OracleScreener
- MarketHealth
- ContrarianRadar
- TrendRadar
- StructureScanner
- TitanRadar
- TitanSignalsPanel

### 2. TanStack Query Configuration

**Optimized for Crypto Data**:

```typescript
{
  staleTime: 120_000,        // 2 min - data stays fresh
  gcTime: 5 * 60_000,        // 5 min - cache retention
  refetchOnWindowFocus: false, // Don't refetch on tab switch
  placeholderData: keepPreviousData, // Smooth transitions
}
```

**Why these values?**:

- **staleTime 120s**: Crypto prices change but not drastically in 2 minutes
- **Aligned with backend cache (180s)**: Reduces unnecessary backend load
- **refetchOnWindowFocus false**: User switches tabs frequently, avoid spam
- **keepPreviousData**: Shows old data while fetching new, smoother UX

### 3. React Optimization (Future)

**Not yet implemented** (but recommended):

- `React.memo()` for expensive components
- `useMemo()` for expensive calculations
- `useCallback()` for stable function references
- Virtualization for long lists (react-window)

---

## Routing

### App Router (Next.js 14)

**Static Routes**:

- `/` - Dashboard home
- `/analytics` - Analytics page

**Dynamic Routes**:

- `/chart/[symbol]` - Chart viewer (e.g., `/chart/BTC-USDT`)

**File Structure**:

```
app/
├── page.tsx              # /
├── layout.tsx            # Root layout
├── analytics/
│   └── page.tsx          # /analytics
└── chart/
    └── [symbol]/
        └── page.tsx      # /chart/:symbol
```

**Navigation**:

```typescript
import Link from "next/link";
import { useRouter } from "next/navigation";

// Link component
<Link href="/analytics">Analytics</Link>

// Programmatic navigation
const router = useRouter();
router.push("/chart/BTC-USDT");
```

---

## Styling

### Tailwind CSS

**Utility-First Approach**:

```tsx
<div className="flex items-center justify-between gap-4 p-6 rounded-xl bg-secondary/30 border border-border/50">
  <h3 className="text-lg font-bold">Title</h3>
  <button className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90">Action</button>
</div>
```

**Custom Theme** (via Tailwind config):

- Color palette defined in `tailwind.config.ts`
- CSS variables for theme switching (light/dark)
- Custom animations (shimmer, pulse)

### Shadcn/ui Components

**Pre-built, customizable** components:

```tsx
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

<Button variant="default" size="lg">Click Me</Button>
<Skeleton className="w-full h-12 rounded" />
```

**Benefits**:

- Consistent design system
- Accessible out of the box
- Fully customizable
- TypeScript support

---

## State Management

### Server State (TanStack Query)

**All API data** managed by TanStack Query:

- Market data (OHLCV, tickers)
- Analytics (screener, health)
- Coin metadata

**Benefits**:

- Automatic caching
- Background refetching
- Loading/error states
- Request deduplication

### Client State (React useState)

**Local component state**:

- UI state (modals, dropdowns open/closed)
- Form inputs
- Filters, search queries
- Active tab selection

**Example**:

```typescript
const [activeTab, setActiveTab] = useState<"screener" | "health">("screener");
const [searchQuery, setSearchQuery] = useState("");
```

### No Global State Library

**Why?**:

- TanStack Query handles server state
- React Context sufficient for theme/settings
- Zustand/Redux unnecessary complexity

---

## TypeScript Patterns

### Interface Definitions

```typescript
// API response types
interface OHLCVResponse {
  symbol: string;
  timeframe: string;
  provider: string;
  candles: Candle[];
}

interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Component props
interface CoinTableProps {
  data: CoinData[];
  onCoinSelect: (coin: CoinData) => void;
}
```

### Type Safety Best Practices

1. **No `any` types** - Always define proper types
2. **Optional properties** - Use `?` for optional fields
3. **Union types** - For multiple possible values
4. **Generics** - For reusable components

```typescript
// Good
interface Props {
  status: "loading" | "success" | "error";
  data?: CoinData;
}

// Bad
interface Props {
  status: any;
  data: any;
}
```

---

## API Client

### Centralized API Layer

**File**: `lib/api.ts`

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchOHLCV(symbol: string, timeframe: string = "1h", limit: number = 100, endTimestamp?: number): Promise<OHLCVResponse> {
  const params = new URLSearchParams({
    timeframe,
    limit: limit.toString(),
    ...(endTimestamp && { end_timestamp: endTimestamp.toString() }),
  });

  const res = await fetch(`${API_URL}/api/ohlcv/${symbol}?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch OHLCV: ${res.statusText}`);
  return res.json();
}
```

**Benefits**:

- **Single source of truth** for API URLs
- **Type-safe** requests and responses
- **Error handling** in one place
- **Easy to mock** for testing

---

## Environment Variables

**File**: `.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Usage**:

```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
```

**Important**:

- Prefix with `NEXT_PUBLIC_` to expose to browser
- Never commit `.env.local` to git
- Use `.env.local.example` for documentation

---

## Development Workflow

### Running Locally

```bash
cd frontend
npm install
npm run dev
```

**Hot Reload**: Changes automatically reflected

### Building for Production

```bash
npm run build
npm run start
```

### Type Checking

```bash
npx tsc --noEmit
```

**Zero errors required** before committing

---

## Testing (Future)

**Not yet implemented**:

- Unit tests (Vitest)
- Component tests (React Testing Library)
- E2E tests (Playwright)

**Recommended Structure**:

```
src/
├── components/
│   └── __tests__/
│       └── CoinTable.test.tsx
├── hooks/
│   └── __tests__/
│       └── useMarketData.test.ts
```

---

## Accessibility

**Current State**: Basic accessibility
**Future Improvements**:

- ARIA labels on interactive elements
- Keyboard navigation
- Screen reader support
- Focus management

---

## Performance Metrics

**Current Performance** (Lighthouse):

- **Not measured yet** - Recommended to run Lighthouse CI

**Target Metrics**:

- First Contentful Paint: <1.5s
- Time to Interactive: <3s
- Largest Contentful Paint: <2.5s
- Cumulative Layout Shift: <0.1

---

## Common Tasks

### Adding a New Page

1. Create file in `app/` directory

   ```typescript
   // app/new-page/page.tsx
   export default function NewPage() {
     return <div>New Page</div>;
   }
   ```

2. Add navigation link
   ```typescript
   <Link href="/new-page">New Page</Link>
   ```

### Adding a New API Hook

1. Define in `hooks/` directory

   ```typescript
   // hooks/useNewData.ts
   export function useNewData(param: string) {
     return useQuery({
       queryKey: ["new-data", param],
       queryFn: () => fetchNewData(param),
       staleTime: 120_000,
     });
   }
   ```

2. Add API client function

   ```typescript
   // lib/api.ts
   export async function fetchNewData(param: string) {
     const res = await fetch(`${API_URL}/api/new-data/${param}`);
     return res.json();
   }
   ```

3. Use in component
   ```typescript
   const { data } = useNewData("param");
   ```

---

## Troubleshooting

### Common Issues

1. **TypeScript errors**
   - Run `npx tsc --noEmit` to see all errors
   - Check for missing type definitions

2. **Build errors**
   - Clear `.next` directory: `rm -rf .next`
   - Reinstall dependencies: `rm -rf node_modules && npm install`

3. **API connection errors**
   - Verify `NEXT_PUBLIC_API_URL` in `.env.local`
   - Check backend is running: `docker compose ps`

4. **Stale data in development**
   - Open React Query DevTools (bottom of page)
   - Click "Invalidate" on specific queries

---

## Future Improvements

- [ ] Add component tests
- [ ] Implement React.memo optimizations
- [ ] Add virtualization for long lists
- [ ] Improve accessibility
- [ ] Add performance monitoring
- [ ] Implement service worker for offline support
- [ ] Add Lighthouse CI to deployment pipeline
