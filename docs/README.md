# Argus Documentation

**Last Updated**: (see CHANGELOG)

---

## Quick Start

**For AI agents or new developers**: Start with [AI_AGENT_GUIDE.md](./AI_AGENT_GUIDE.md)

**For trading / using the app**: Start with [SLASH_COMMANDS.md](./SLASH_COMMANDS.md)

---

## Document Index

### Using Argus

| Document | Description |
|---|---|
| [SLASH_COMMANDS.md](./SLASH_COMMANDS.md) | `/read` command guide — how to generate coin and market reports, interpret signals, read the chart, spot setup and HODL analysis |

### Backend

| Document | Description |
|---|---|
| [backend/API.md](./backend/API.md) | Full REST API reference — all endpoints, parameters, response fields |
| [backend/ARCHITECTURE.md](./backend/ARCHITECTURE.md) | Backend system design and data flow |
| [backend/DATA_ARCHITECTURE.md](./backend/DATA_ARCHITECTURE.md) | Data storage, caching strategy, Redis/Postgres usage |
| [backend/ERROR_HANDLING.md](./backend/ERROR_HANDLING.md) | Custom exception hierarchy and logging patterns |
| [backend/TROUBLESHOOTING.md](./backend/TROUBLESHOOTING.md) | Common issues and fixes |
| [backend/COIN_METADATA_SYNC.md](./backend/COIN_METADATA_SYNC.md) | Coin metadata sync from CoinGecko |
| [DOCKER_PERMISSIONS.md](./DOCKER_PERMISSIONS.md) | Docker volume permission setup |

### Frontend

| Document | Description |
|---|---|
| [frontend/ARCHITECTURE.md](./frontend/ARCHITECTURE.md) | Frontend patterns, component structure, state management |
| [frontend/TESTING.md](./frontend/TESTING.md) | Frontend testing guide |

### Analytics & Strategies

| Document | Description |
|---|---|
| [strategies/OVERVIEW.md](./strategies/OVERVIEW.md) | Oracle + Titan strategies overview, voting table, backtest methodology, multi-timeframe framework |
| [analytics/ORACLE_SCREENER.md](./analytics/ORACLE_SCREENER.md) | Oracle Screener deep-dive — voter logic, scoring, signal synthesis |
| [analytics/TITAN_STRATEGY.md](./analytics/TITAN_STRATEGY.md) | Titan strategy — signal types, confidence scoring, indicator stack |
| [analytics/TITAN_SIGNALS.md](./analytics/TITAN_SIGNALS.md) | Titan Signals panel documentation |
| [analytics/CONTRARIAN_RADAR.md](./analytics/CONTRARIAN_RADAR.md) | Contrarian Radar — ATR mean-reversion logic |

### Project Management

| Document | Description |
|---|---|
| [CHANGELOG.md](./CHANGELOG.md) | Version history |

---

## Find What You Need

### "I want to analyze a coin or the market"
→ [SLASH_COMMANDS.md](./SLASH_COMMANDS.md) — run `/read BTC` or `/read market`

### "I want to understand the trading signals"
→ [SLASH_COMMANDS.md — How to Read the Report](./SLASH_COMMANDS.md#how-to-read-the-report)
→ [strategies/OVERVIEW.md](./strategies/OVERVIEW.md)

### "I want to buy a coin and hold long term"
→ [SLASH_COMMANDS.md — Long-Term / HODL Section](./SLASH_COMMANDS.md#long-term--hodl-section)
→ Run `/read ETH hold`

### "I want to understand the codebase"
→ [AI_AGENT_GUIDE.md](./AI_AGENT_GUIDE.md)

### "I want to add a new API endpoint"
→ [AI_AGENT_GUIDE.md — Common Tasks](./AI_AGENT_GUIDE.md#common-tasks)
→ [backend/API.md](./backend/API.md)

### "I'm getting errors"
→ [backend/ERROR_HANDLING.md](./backend/ERROR_HANDLING.md)
→ [backend/TROUBLESHOOTING.md](./backend/TROUBLESHOOTING.md)

### "I want to understand data flow and caching"
→ [backend/DATA_ARCHITECTURE.md](./backend/DATA_ARCHITECTURE.md)
→ [backend/ARCHITECTURE.md](./backend/ARCHITECTURE.md)
