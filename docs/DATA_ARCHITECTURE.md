# Argus Data Architecture

## Overview

This document details the data flow architecture for Argus, focusing on how market data is fetched, stored, and served to users. The design follows modern event-driven patterns for scalability and reliability.

---

## Architecture Diagram

> **Note**: For details on how we handle coin metadata (logos/names) vs real-time prices, see [Coin Metadata Sync & Hybrid Architecture](./COIN_METADATA_SYNC.md).

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        UI[React UI]
        RQ[React Query]
        IS[Infinite Scroll]
    end

    subgraph "API Layer (FastAPI)"
        API[REST Endpoints]
        OD[On-Demand Fetch]
    end

    subgraph "Data Stores"
        Redis[(Redis Cache)]
        PG[(PostgreSQL)]
    end

    subgraph "Background Jobs (Arq Worker)"
        Worker[sync_market_summary<br/>Every 30s]
    end

    subgraph "External APIs"
        Binance[Binance API]
    end

    UI --> RQ
    RQ -->|HTTP GET| API
    IS -->|fetchNextPage| RQ

    API -->|Market Summary| Redis
    API -->|OHLCV History| PG
    API -->|Missing Data?| OD
    OD -->|Direct Fetch + Save| Binance
    OD -->|UPSERT| PG

    Worker -->|fetch_all_tickers| Binance
    Worker -->|SET market:tickers| Redis
    Worker -->|SET market:summary| Redis
```

---

## Data Flow Patterns

### 1. Hybrid Market State (Snapshot + Live Overlay)

**Pattern**: Periodic Snapshot (CoinGecko) + Real-Time Overlay (Binance)
**Storage**: Redis

This architecture solves the "Coverage vs Speed" dilemma. We use CoinGecko for broad coverage (1000+ coins, metadata) and Binance for real-time speed (top 300 coins).

```mermaid
graph LR
    subgraph "Ingestion Layers"
        CG[CoinGecko Snapshot Worker]
        BN[Binance Live Worker]
    end

    subgraph "Redis Storage"
        Snapshot[market:snapshot]
        Live[market:tickers]
    end

    subgraph "Serving Layer"
        API[API Endpoint]
    end

    CG --"Every 5 mins (Base state)"--> Snapshot
    BN --"Every 30s (Live prices)"--> Live

    API --"Reads & Merges"--> Snapshot
    API --"Reads & Merges"--> Live

    Snapshot --"Merged Response"--> API
    Live --"Merged Response"--> API
```

**Why This Approach?**

1.  **Massive Coverage**: We get 1000+ coins from CoinGecko (Base State).
2.  **Real-Time Speed**: Top 300 active coins get live price updates from Binance.
3.  **Rate Limit Safe**: We only hit CoinGecko once every 5 minutes (server-side), completely safe.
4.  **Single Source of Truth**: Frontend never guesses; it gets one merged list from the API.

---

### 2. Real-Time Ticker Data (Hot Path)

**Pattern**: Worker → Redis → API → Frontend
**Latency**: < 50ms

```mermaid
sequenceDiagram
    participant Worker
    participant Binance
    participant Redis(Live)
    participant Redis(Base)
    participant API
    participant Frontend

    loop Every 30 seconds
        Worker->>Binance: fetch_all_tickers()
        Binance-->>Worker: [300 live tickers]
        Worker->>Redis(Live): SET market:tickers [JSON]
    end

    Frontend->>API: GET /api/market/summary
    API->>Redis(Base): GET market:snapshot (1000 coins)
    API->>Redis(Live): GET market:tickers (Top 300 live)
    Note over API: Merge Live into Base
    API-->>Frontend: 200 OK (Merged List)
```

**Why This Approach?**

- ✅ **Low latency**: Redis provides sub-millisecond reads
- ✅ **No rate limits**: Frontend never hits external APIs
- ✅ **Cached for all users**: Single source of truth

---

### 2. Historical OHLCV Data (Cold Path)

**Pattern**: Frontend → API → PostgreSQL (+ On-Demand Binance Fetch)
**Latency**: < 100ms (cached) / < 2s (fetching new data)

```mermaid
sequenceDiagram
    participant Frontend
    participant API
    participant PostgreSQL
    participant Binance

    Frontend->>API: GET /api/ohlcv/BTC/USDT?timeframe=1h&limit=1000

    API->>PostgreSQL: SELECT * FROM candles WHERE symbol=... LIMIT 1000
    PostgreSQL-->>API: [1000 candles]
    API-->>Frontend: 200 OK

    Note over Frontend: User scrolls left (older data)

    Frontend->>API: GET /api/ohlcv/BTC/USDT?end_timestamp=1764000000000
    API->>PostgreSQL: SELECT * FROM candles WHERE timestamp < end_timestamp
    PostgreSQL-->>API: [0 candles] ⚠️ Missing!

    Note over API: On-Demand Fetch Triggered

    API->>Binance: fetch_ohlcv(since=calculated_timestamp)
    Binance-->>API: [1000 candles]
    API->>PostgreSQL: UPSERT candles
    API->>PostgreSQL: SELECT * (re-query)
    PostgreSQL-->>API: [1000 candles]
    API-->>Frontend: 200 OK
```

**Why This Approach?**

- ✅ **Lazy loading**: Only fetch data when user needs it
- ✅ **Persistent storage**: Historical data never re-fetched
- ✅ **Pagination support**: `end_timestamp` enables infinite scroll

---

### 3. Infinite Scroll Implementation

**Pattern**: Frontend State → Visible Range Detection → API Pagination

```mermaid
sequenceDiagram
    participant Chart
    participant useInfiniteQuery
    participant API

    Note over Chart: User scrolls to left edge

    Chart->>Chart: subscribeVisibleLogicalRangeChange()
    Chart->>Chart: range.from < 10 ?

    alt Near left edge
        Chart->>useInfiniteQuery: onLoadMore()
        useInfiniteQuery->>useInfiniteQuery: hasNextPage? ✓
        useInfiniteQuery->>API: GET /ohlcv?end_timestamp=oldest_candle
        API-->>useInfiniteQuery: {candles: [...]}
        useInfiniteQuery->>Chart: setData(merged_candles)
        Chart->>Chart: setVisibleLogicalRange(saved_range)
    end
```

**Key Implementation Details:**

- `useInfiniteQuery` manages pagination state
- `getNextPageParam` returns oldest candle's timestamp
- **Closure fix**: `onLoadMoreRef` prevents stale state

---

## Storage Strategy

### Redis (Hot Data)

| Key               | TTL                   | Contents                            |
| ----------------- | --------------------- | ----------------------------------- |
| `market:tickers`  | ∞ (updated every 30s) | Live prices + 24h changes (Binance) |
| `market:snapshot` | ∞ (updated every 5m)  | Base market state (CoinGecko)       |
| `market:summary`  | ∞ (updated every 30s) | Total volume, top gainers/losers    |
| `ticker:{symbol}` | Optional              | Individual ticker price             |

### PostgreSQL (Cold Data)

| Table     | Primary Key                                | Indexed Columns                    |
| --------- | ------------------------------------------ | ---------------------------------- |
| `candles` | `(symbol, provider, timeframe, timestamp)` | `symbol`, `timeframe`, `timestamp` |

**Upsert Strategy**: `session.merge()` ensures no duplicates

---

## Modern Standards Compliance

### ✅ Patterns We Follow

| Pattern                             | Implementation                               |
| ----------------------------------- | -------------------------------------------- |
| **CQRS** (Command Query Separation) | Worker writes, API reads                     |
| **Event-Driven Architecture**       | Jobs triggered by scheduler/API              |
| **Cache-Aside Pattern**             | API reads cache first, fetches on miss       |
| **Lazy Loading**                    | Data fetched only when user scrolls          |
| **Optimistic UI**                   | Chart preserves scroll position during loads |

### ✅ Best Practices

1. **Decoupled Ingestion**: Worker is separate from API
2. **Rate Limit Handling**: Worker respects Binance limits
3. **Idempotent Operations**: Upsert prevents duplicates
4. **Graceful Degradation**: API returns cached data if Binance fails
5. **Pagination**: Timestamp-based cursor pagination

### ⚠️ Potential Improvements

| Area                   | Current           | Recommended                         |
| ---------------------- | ----------------- | ----------------------------------- |
| **WebSocket**          | Polling every 60s | Real-time push for tickers          |
| **Data Compression**   | None              | gzip for large OHLCV responses      |
| **Cache Invalidation** | TTL-based         | Pub/Sub for instant updates         |
| **Horizontal Scaling** | Single worker     | Multiple workers with Redis locking |

---

## File Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── routes/
│   │   └── market.py        # API endpoints
│   ├── providers/
│   │   └── binance_provider.py
│   ├── schemas/
│   │   └── candle.py        # SQLModel
│   ├── storage.py           # Redis/DB managers
│   └── worker.py            # Arq worker
└── scripts/
    └── backfill_history.py  # Bulk data migration
```

---

## Conclusion

The Argus data architecture follows modern best practices:

- **Separation of concerns** between ingestion and serving
- **Hybrid storage** (Redis for speed, Postgres for persistence)
- **On-demand fetching** to minimize upfront data load
- **Infinite scroll** with proper state management

The system is designed to scale horizontally and can be extended with WebSocket support for real-time updates.
