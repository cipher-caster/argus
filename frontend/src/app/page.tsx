"use client";

/**
 * Argus Dashboard
 * Professional CoinGlass-style layout
 */

import { CoinTable } from "@/components/CoinTable";
import { StatsCards } from "@/components/StatsCards";
import { TopCoinsWidgets } from "@/components/TopCoinsWidgets";
import { useProvider } from "@/hooks/useMarketData";
import { useCoins, useMarketSummary } from "@/hooks/useMarketOverview";
import { useState } from "react";

export default function MarketOverview() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("market_cap");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const pageSize = 50;

  const { data: providerData } = useProvider();
  const { data: summary } = useMarketSummary();
  const { data: coinsData, isLoading } = useCoins({
    page,
    pageSize,
    search: search || undefined,
    sortBy,
    sortOrder,
  });

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
    setPage(1);
  };

  const totalPages = coinsData ? Math.ceil(coinsData.total / pageSize) : 1;

  return (
    <div className="app">
      {/* Main Content */}
      <main className="container">
        {/* Market Highlights */}
        <section className="section">
          <StatsCards coins={coinsData?.coins || []} isLoading={isLoading} />
        </section>

        {/* Widgets Section */}
        <section className="section">
          <h2 className="section-title">Cryptocurrency Data Analysis</h2>
          <TopCoinsWidgets coins={coinsData?.coins || []} isLoading={isLoading} />
        </section>

        {/* Main Table */}
        <section className="section">
          <CoinTable coins={coinsData?.coins || []} isLoading={isLoading} sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button className="page-btn" onClick={() => setPage(1)} disabled={page === 1}>
                First
              </button>
              <button className="page-btn" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
                ← Prev
              </button>
              <span className="page-info">
                Page <strong>{page}</strong> of <strong>{totalPages}</strong>
              </span>
              <button className="page-btn" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
                Next →
              </button>
            </div>
          )}
        </section>
      </main>

      <style jsx>{`
        .app {
          min-height: 100vh;
          background: var(--bg-primary);
        }

        /* Navbar */
        .navbar {
          position: sticky;
          top: 0;
          z-index: 100;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-color);
          height: 60px;
        }

        .navbar-inner {
          max-width: 1440px;
          margin: 0 auto;
          padding: 0 24px;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .nav-left {
          display: flex;
          align-items: center;
          gap: 32px;
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 20px;
          font-weight: 800;
          color: var(--text-primary);
          cursor: pointer;
        }
        .brand-icon {
          color: var(--accent-primary);
          font-size: 22px;
        }

        .nav-links {
          display: flex;
          gap: 24px;
        }
        .nav-link {
          font-size: 14px;
          font-weight: 500;
          color: var(--text-secondary);
          cursor: pointer;
          transition: color 0.2s;
        }
        .nav-link:hover,
        .nav-link.active {
          color: var(--text-primary);
        }

        .nav-right {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .search-bar {
          position: relative;
          background: var(--bg-tertiary);
          border-radius: 8px;
          padding: 6px 12px;
          display: flex;
          align-items: center;
          gap: 8px;
          border: 1px solid transparent;
        }
        .search-bar:focus-within {
          border-color: var(--accent-primary);
        }
        .search-icon {
          font-size: 12px;
          opacity: 0.5;
        }
        .search-bar input {
          background: none;
          border: none;
          outline: none;
          color: var(--text-primary);
          font-size: 13px;
          width: 160px;
        }

        .connect-btn {
          padding: 8px 16px;
          background: var(--text-primary);
          color: var(--bg-primary);
          border: none;
          border-radius: 6px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
        }

        /* Container */
        .container {
          max-width: 1440px;
          margin: 0 auto;
          padding: 24px;
        }

        .section {
          margin-bottom: 32px;
        }
        .section-title {
          font-size: 20px;
          font-weight: 700;
          color: var(--text-primary);
          margin-bottom: 20px;
        }

        /* Pagination */
        .pagination {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          margin-top: 24px;
          padding: 20px;
        }

        .page-btn {
          padding: 8px 16px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
          color: var(--text-primary);
          cursor: pointer;
          transition: all 0.2s;
        }

        .page-btn:hover:not(:disabled) {
          background: var(--accent-primary);
          border-color: var(--accent-primary);
          color: white;
        }

        .page-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }

        .page-info {
          font-size: 13px;
          color: var(--text-secondary);
          padding: 0 16px;
        }

        .page-info strong {
          color: var(--text-primary);
        }
      `}</style>
    </div>
  );
}
