"use client";

import { Panel } from "@/components/ui";
import { useWatchlistStore } from "@/stores/watchlistStore";
import { Plus, Search, Star, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

interface WatchlistPanelProps {
  currentSymbol?: string;
}

interface TickerData {
  symbol: string;
  price: number;
  change_24h: number;
}

export function WatchlistPanel({ currentSymbol }: WatchlistPanelProps) {
  const { items, removeSymbol, addSymbol } = useWatchlistStore();
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [tickerData, setTickerData] = useState<Record<string, TickerData>>({});

  // Fetch live prices for watchlist items
  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    async function fetchPrices() {
      try {
        const res = await fetch(`${apiUrl}/api/market/tickers`);
        if (!res.ok) return;
        const data = await res.json();
        const priceMap: Record<string, TickerData> = {};
        data.tickers?.forEach((t: TickerData) => {
          priceMap[t.symbol] = t;
        });
        setTickerData(priceMap);
      } catch (e) {
        console.error("Failed to fetch tickers", e);
      }
    }
    fetchPrices();
    const interval = setInterval(fetchPrices, 10000);
    return () => clearInterval(interval);
  }, []);

  const filteredItems = searchQuery ? items.filter((item) => item.symbol.toLowerCase().includes(searchQuery.toLowerCase())) : items;

  return (
    <div className="watchlist-container">
      <Panel
        title="Watchlist"
        headerAction={
          <button className="btn btn-ghost btn-sm" onClick={() => setSearchOpen(!searchOpen)}>
            {searchOpen ? <X size={14} /> : <Plus size={14} />}
          </button>
        }
      >
        {searchOpen && (
          <div className="watchlist-search">
            <Search size={14} />
            <input
              className="input"
              placeholder="Add symbol..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && searchQuery) {
                  const formatted = searchQuery.toUpperCase().includes("/") ? searchQuery.toUpperCase() : `${searchQuery.toUpperCase()}/USDT`;
                  addSymbol(formatted);
                  setSearchQuery("");
                  setSearchOpen(false);
                }
              }}
            />
          </div>
        )}

        <div className="watchlist-items">
          {filteredItems.map((item) => {
            const ticker = tickerData[item.symbol];
            const isActive = currentSymbol === item.symbol;
            const urlSymbol = item.symbol.replace("/", "-");

            return (
              <Link key={item.symbol} href={`/chart/${urlSymbol}`} className={`watchlist-item ${isActive ? "active" : ""}`}>
                <div className="watchlist-left">
                  <Star size={12} fill={isActive ? "var(--accent-primary)" : "none"} />
                  <span className="watchlist-symbol">{item.symbol.replace("/USDT", "")}</span>
                </div>
                <div className="watchlist-right">
                  <span className="watchlist-price">{ticker?.price?.toLocaleString(undefined, { maximumFractionDigits: 2 }) || "—"}</span>
                  <span className={`watchlist-change ${(ticker?.change_24h || 0) >= 0 ? "positive" : "negative"}`}>{ticker?.change_24h?.toFixed(2) || "0.00"}%</span>
                </div>
                <button
                  className="watchlist-remove"
                  onClick={(e) => {
                    e.preventDefault();
                    removeSymbol(item.symbol);
                  }}
                >
                  <X size={12} />
                </button>
              </Link>
            );
          })}
        </div>
      </Panel>

      <style jsx>{`
        .watchlist-container {
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        .watchlist-search {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem;
          border-bottom: 1px solid var(--border-color);
        }
        .watchlist-search .input {
          flex: 1;
          padding: 0.375rem 0.5rem;
          font-size: 0.75rem;
        }
        .watchlist-items {
          flex: 1;
          overflow-y: auto;
        }
        .watchlist-left {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .watchlist-right {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 2px;
        }
        .watchlist-remove {
          opacity: 0;
          background: none;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          padding: 4px;
        }
        .watchlist-item:hover .watchlist-remove {
          opacity: 1;
        }
      `}</style>
    </div>
  );
}
