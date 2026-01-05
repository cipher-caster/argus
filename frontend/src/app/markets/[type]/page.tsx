"use client";

import { CoinTable } from "@/components/CoinTable";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useCoins } from "@/hooks/useMarketOverview";
import { ArrowLeft, LayoutDashboard } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

export default function MarketCategoryPage() {
  const params = useParams();
  const type = params.type as string;

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  // Default Sort Configuration based on type
  const getDefaultSort = () => {
    switch (type) {
      case "gainers":
        return { sortBy: "change_24h", sortOrder: "desc" };
      case "losers":
        return { sortBy: "change_24h", sortOrder: "asc" };
      case "volume":
        return { sortBy: "volume_24h", sortOrder: "desc" };
      default:
        return { sortBy: "price", sortOrder: "desc" }; // Fallback
    }
  };

  const defaultSort = getDefaultSort();
  const [sortBy, setSortBy] = useState(defaultSort.sortBy);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">(defaultSort.sortOrder as "asc" | "desc");
  const pageSize = 50;

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

  const getTitle = () => {
    switch (type) {
      case "gainers":
        return "Top Gainers";
      case "losers":
        return "Top Losers";
      case "volume":
        return "Volume Leaders";
      default:
        return "Market Data";
    }
  };

  return (
    <div className="app">
      {/* Navbar (Simplified) */}
      <nav className="navbar">
        <div className="navbar-inner">
          <div className="nav-left">
            <Link href="/" className="brand">
              <LayoutDashboard size={24} className="brand-icon" />
              <span className="brand-name">Argus</span>
            </Link>
          </div>
          <div className="nav-right">
            <ThemeToggle />
          </div>
        </div>
      </nav>

      <main className="container">
        <div className="header-row">
          <Link href="/" className="back-link">
            <ArrowLeft size={16} /> Back to Overview
          </Link>
          <h1 className="page-title">{getTitle()}</h1>
        </div>

        <section className="section">
          {/* Reusing existing list, effectively creates a full table view */}
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
        .navbar {
          height: 60px;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-color);
          display: flex;
          align-items: center;
        }
        .navbar-inner {
          width: 100%;
          max-width: 1440px;
          margin: 0 auto;
          padding: 0 24px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .brand {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 20px;
          font-weight: 800;
          color: var(--text-primary);
          text-decoration: none;
        }
        .brand-icon {
          color: var(--accent-primary);
        }
        .container {
          max-width: 1440px;
          margin: 0 auto;
          padding: 24px;
        }

        .header-row {
          margin-bottom: 24px;
        }
        .back-link {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          color: var(--text-secondary);
          text-decoration: none;
          font-size: 14px;
          margin-bottom: 12px;
          transition: color 0.2s;
        }
        .back-link:hover {
          color: var(--text-primary);
        }
        .page-title {
          font-size: 24px;
          font-weight: 700;
          color: var(--text-primary);
        }

        .pagination {
          display: flex;
          justify-content: center;
          gap: 12px;
          margin-top: 24px;
        }
        .page-btn {
          padding: 8px 16px;
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          color: var(--text-primary);
          cursor: pointer;
        }
        .page-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .page-info {
          color: var(--text-secondary);
          display: flex;
          align-items: center;
        }
        .page-info strong {
          color: var(--text-primary);
          margin: 0 4px;
        }
      `}</style>
    </div>
  );
}
