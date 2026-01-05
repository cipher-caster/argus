"use client";

/**
 * Coin Table Component
 * Professional CoinGlass-style table with rich data
 */

import { CoinInfo } from "@/lib/marketApi";
import { ArrowDown, ArrowUp, ArrowUpDown, Search, Star } from "lucide-react";
import Link from "next/link";
import { memo, useEffect, useState } from "react";

interface CoinTableProps {
  coins: CoinInfo[];
  isLoading: boolean;
  sortBy: string;
  sortOrder: string;
  onSort: (field: string) => void;
}

function CoinTableComponent({ coins, isLoading, sortBy, sortOrder, onSort }: CoinTableProps) {
  const [favorites, setFavorites] = useState<string[]>([]);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem("argus_favorites");
    if (stored) {
      try {
        setFavorites(JSON.parse(stored));
      } catch (e) {
        console.error("Failed to parse favorites", e);
      }
    }
  }, []);

  const toggleFavorite = (symbol: string) => {
    const newFavorites = favorites.includes(symbol) ? favorites.filter((s) => s !== symbol) : [...favorites, symbol];
    setFavorites(newFavorites);
    localStorage.setItem("argus_favorites", JSON.stringify(newFavorites));
  };

  const SortIcon = ({ field }: { field: string }) => {
    if (sortBy !== field) return <ArrowUpDown size={12} className="sort-icon inactive" />;
    return sortOrder === "asc" ? <ArrowUp size={12} className="sort-icon active" /> : <ArrowDown size={12} className="sort-icon active" />;
  };

  const formatPrice = (price: number) => {
    if (price >= 1000) {
      return price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } else if (price >= 1) {
      return price.toFixed(2);
    } else if (price >= 0.0001) {
      return price.toFixed(5);
    } else {
      return price.toFixed(8);
    }
  };

  const formatVolume = (vol: number | null) => {
    if (!vol) return "—";
    if (vol >= 1e9) return `$${(vol / 1e9).toFixed(2)}B`;
    if (vol >= 1e6) return `$${(vol / 1e6).toFixed(2)}M`;
    return `$${(vol / 1e3).toFixed(0)}K`;
  };

  if (!mounted) return <div className="table-container" style={{ height: "400px" }}></div>;

  return (
    <div className="table-container">
      {/* 
      <div className="table-header-controls">
        <div className="tabs">
          <button className="tab active">Favorites</button>
          <button className="tab">Spot</button>
          <button className="tab">Derivatives</button>
        </div>
        <div className="table-actions">
          <button className="action-btn">Filter</button>
          <button className="action-btn">Customize</button>
        </div>
      </div>
      */}

      <table className="table">
        <thead>
          <tr>
            <th className="col-star"></th>
            <th className="col-rank">#</th>
            <th className="col-name sortable" onClick={() => onSort("symbol")}>
              <div className="th-content">
                Symbol <SortIcon field="symbol" />
              </div>
            </th>

            <th className="col-price sortable" onClick={() => onSort("price")}>
              <div className="th-content right">
                Price <SortIcon field="price" />
              </div>
            </th>
            <th className="col-change">24h Change</th>
            <th className="col-vol sortable" onClick={() => onSort("volume_24h")}>
              <div className="th-content right">
                Volume (24h) <SortIcon field="volume_24h" />
              </div>
            </th>
            <th className="col-market sortable" onClick={() => onSort("market_cap")}>
              <div className="th-content right">
                Market Cap <SortIcon field="market_cap" />
              </div>
            </th>
            <th className="col-high">24h High</th>
            <th className="col-low">24h Low</th>
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            Array.from({ length: 15 }).map((_, i) => (
              <tr key={i} className="row-skeleton">
                <td>
                  <div className="skeleton skeleton-sm" />
                </td>
                <td>
                  <div className="skeleton-coin">
                    <div className="skeleton skeleton-avatar" />
                    <div className="skeleton skeleton-text" />
                  </div>
                </td>
                <td>
                  <div className="skeleton skeleton-price" />
                </td>
                <td>
                  <div className="skeleton skeleton-badge" />
                </td>
                <td>
                  <div className="skeleton skeleton-price" />
                </td>
                <td>
                  <div className="skeleton skeleton-price" />
                </td>
                <td>
                  <div className="skeleton skeleton-price" />
                </td>
              </tr>
            ))
          ) : coins.length === 0 ? (
            <tr>
              <td colSpan={9} className="empty-state">
                <div className="empty-icon">
                  <Search size={32} />
                </div>
                <div className="empty-text">No coins found matching criteria</div>
              </td>
            </tr>
          ) : (
            coins.map((coin) => {
              const isFav = favorites.includes(coin.symbol);
              return (
                <tr key={coin.symbol} className="row-data">
                  <td className="col-star">
                    <Star size={14} className={`star-icon ${isFav ? "active" : ""}`} onClick={() => toggleFavorite(coin.symbol)} />
                  </td>
                  <td className="col-rank">{coin.rank}</td>
                  <td className="col-name">
                    <Link href={`/chart/${coin.symbol.replace("/", "-")}`} className="coin-link">
                      <div className="coin-avatar">{coin.name.slice(0, 1)}</div>
                      <span className="coin-symbol">{coin.symbol}</span>
                    </Link>
                  </td>

                  <td className="col-price">
                    <span className="price">${formatPrice(coin.price)}</span>
                  </td>
                  <td className="col-change">
                    <div className={`change-badge ${(coin.change_24h ?? 0) >= 0 ? "positive" : "negative"}`}>{coin.change_24h !== null ? `${coin.change_24h >= 0 ? "+" : ""}${coin.change_24h.toFixed(2)}%` : "—"}</div>
                  </td>
                  <td className="col-vol">{formatVolume(coin.volume_24h)}</td>
                  <td className="col-market font-mono font-bold">{formatVolume(coin.market_cap)}</td>
                  <td className="col-high text-muted">${formatPrice(coin.high_24h || 0)}</td>
                  <td className="col-low text-muted">${formatPrice(coin.low_24h || 0)}</td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>

      <style jsx>{`
        .table-container {
          background: var(--bg-secondary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .table-header-controls {
          padding: 16px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: var(--bg-secondary);
        }

        .tabs {
          display: flex;
          gap: 24px;
        }
        .tab {
          background: none;
          border: none;
          font-size: 14px;
          font-weight: 600;
          color: var(--text-muted);
          cursor: pointer;
          padding-bottom: 4px;
          border-bottom: 2px solid transparent;
        }
        .tab.active {
          color: var(--text-primary);
          border-bottom-color: var(--accent-primary);
        }

        .table-actions {
          display: flex;
          gap: 12px;
        }
        .action-btn {
          padding: 6px 12px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 6px;
          font-size: 12px;
          font-weight: 500;
          color: var(--text-secondary);
          cursor: pointer;
        }

        .table {
          width: 100%;
          border-collapse: collapse;
        }

        /* Header */
        thead tr {
          background: var(--bg-tertiary);
        }
        th {
          padding: 12px 16px;
          font-size: 11px;
          font-weight: 600;
          color: var(--text-muted);
          text-transform: uppercase;
          border-bottom: 1px solid var(--border-color);
          white-space: nowrap;
        }

        .th-content {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .th-content.right {
          justify-content: flex-end;
        }

        th.sortable {
          cursor: pointer;
          user-select: none;
        }
        th.sortable:hover {
          color: var(--text-primary);
        }

        .sort-icon {
          opacity: 0.3;
          transition: opacity 0.2s;
        }
        .sort-icon.active {
          opacity: 1;
          color: var(--accent-primary);
        }

        /* Rows */
        /* Rows */
        .row-data {
          transition: background 0.15s;
          cursor: pointer;
        }
        .row-data:hover {
          background: var(--bg-tertiary);
        }
        td {
          padding: 14px 16px;
          border-bottom: 1px solid var(--border-color);
          vertical-align: middle;
          text-align: right;
          font-size: 13px;
          color: var(--text-primary);
        }

        /* Specific Column Alignments */
        .col-star,
        .col-rank,
        .col-name {
          text-align: left;
        }

        /* Columns */
        .col-star {
          width: 32px;
          padding-right: 0;
          text-align: center;
        }
        .col-rank {
          color: var(--text-muted);
          font-family: monospace;
          width: 40px;
          text-align: center;
        }

        :global(.star-icon) {
          margin-right: 8px;
          cursor: pointer;
          color: var(--text-muted);
          transition: color 0.2s;
        }
        :global(.star-icon:hover) {
          color: var(--warning);
        }
        :global(.star-icon.active) {
          color: #f59e0b; /* Amber-500 */
          fill: #f59e0b;
        }

        .coin-link {
          display: flex;
          flex-direction: row;
          align-items: center;
          gap: 12px;
          text-decoration: none !important;
          color: inherit !important;
          white-space: nowrap;
          justify-content: flex-start;
          width: 100%;
        }
        .coin-link:hover,
        .coin-link:visited,
        .coin-link:active {
          text-decoration: none !important;
          color: inherit !important;
        }

        .coin-avatar {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          background: var(--accent-primary);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: 800;
          flex-shrink: 0;
        }

        .coin-symbol {
          font-weight: 700;
          font-size: 14px;
          color: var(--text-primary);
        }

        /* Legacy .coin-info-row removed */

        /* Legacy .coin-symbol removed or repurposed */
        .col-price {
          font-family: "SF Mono", monospace;
          font-weight: 600;
        }

        .change-badge {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 4px;
          font-family: "SF Mono", monospace;
          font-weight: 600;
          min-width: 70px;
          text-align: center;
        }
        .change-badge.positive {
          background: rgba(16, 185, 129, 0.15);
          color: var(--success);
        }
        .change-badge.negative {
          background: rgba(239, 68, 68, 0.15);
          color: var(--danger);
        }

        .col-vol {
          font-family: "SF Mono", monospace;
        }
        .text-muted {
          color: var(--text-muted);
        }

        /* Loading */
        .skeleton {
          background: var(--bg-tertiary);
          border-radius: 4px;
          height: 14px;
          animation: shimmer 1.5s infinite;
        }
        .skeleton-avatar {
          width: 28px;
          height: 28px;
          border-radius: 50%;
        }
        .skeleton-text {
          width: 80px;
        }
        .skeleton-badge {
          width: 60px;
          height: 24px;
          margin-left: auto;
        }

        @keyframes shimmer {
          0% {
            opacity: 0.5;
          }
          50% {
            opacity: 0.8;
          }
          100% {
            opacity: 0.5;
          }
        }
      `}</style>
    </div>
  );
}

export const CoinTable = memo(CoinTableComponent);
