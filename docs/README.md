# Argus Documentation 🛡️

Welcome to the official documentation for **Argus**, a professional cryptocurrency dashboard. This folder contains all architectural maps, technical specifications, and development guides.

## 📌 Quick Links

- **[Context & Status](./CONTEXT.md)**: Start here for a high-level overview of the project and current feature status.
- **[Roadmap](./ROADMAP.md)**: Explore the project's milestones, completed phases, and future plans.
- **[Changelog](./CHANGELOG.md)**: Track all notable changes, fixes, and updates.

## 🏗️ Architecture & Data (Backend)

- **[Architecture](./backend/ARCHITECTURE.md)**: High-level overview of the system design.
- **[Data Architecture](./backend/DATA_ARCHITECTURE.md)**: Deep dive into the event-driven data flow, Redis caching, and PostgreSQL persistence.
- **[Coin Metadata Sync](./backend/COIN_METADATA_SYNC.md)**: Details on the "Hybrid Architecture" merging Binance prices with CoinGecko metadata.
- **[API Documentation](./backend/API.md)**: RESTful API endpoints for market data, indicators, and analytics.

## 🛠️ Developer Resources

- **[Testing Guide](./frontend/TESTING.md)**: Documentation on Backend unit tests and Frontend E2E (Playwright) suites.
- **[Troubleshooting](./backend/TROUBLESHOOTING.md)**: Common issues, "gotchas," and how to fix them.
- **[Trading Strategies](./strategies/OVERVIEW.md)**: Technical breakdown of the AI strategy engines.
- **[Analytics Services](./ANALYTICS_SERVICE.md)**: Guide to the Oracle Intelligence suite (Screener, Radar, Health).

---

_For setup instructions, please refer to the root `README.md`._
