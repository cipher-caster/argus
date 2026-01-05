"use client";

/**
 * Symbol/Coin Selector Component
 */

import { SymbolInfo } from "@/lib/api";
import { memo, useMemo, useState } from "react";

interface SymbolSelectorProps {
  symbols: SymbolInfo[];
  selected: string;
  onChange: (symbol: string) => void;
  isLoading?: boolean;
}

// Popular coins to show at top
const FAVORITES = ["BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX", "DOT", "LINK"];

function SymbolSelectorComponent({ symbols, selected, onChange, isLoading }: SymbolSelectorProps) {
  const [search, setSearch] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const filteredSymbols = useMemo(() => {
    if (!symbols.length) return [];

    const searchLower = search.toLowerCase();
    const filtered = symbols.filter((s) => s.base.toLowerCase().includes(searchLower) || s.symbol.toLowerCase().includes(searchLower));

    // Sort: favorites first, then alphabetically
    return filtered.sort((a, b) => {
      const aFav = FAVORITES.indexOf(a.base);
      const bFav = FAVORITES.indexOf(b.base);

      if (aFav !== -1 && bFav !== -1) return aFav - bFav;
      if (aFav !== -1) return -1;
      if (bFav !== -1) return 1;
      return a.base.localeCompare(b.base);
    });
  }, [symbols, search]);

  const selectedSymbol = symbols.find((s) => s.symbol === selected);

  return (
    <div className="symbol-selector">
      <button className="selector-trigger" onClick={() => setIsOpen(!isOpen)}>
        <span className="selected-symbol">{selectedSymbol?.base || "BTC"}/USDT</span>
        <svg className={`chevron ${isOpen ? "open" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="dropdown">
          <input type="text" className="search-input" placeholder="Search coins..." value={search} onChange={(e) => setSearch(e.target.value)} autoFocus />

          <div className="symbol-list">
            {isLoading ? (
              <div className="loading">Loading symbols...</div>
            ) : (
              filteredSymbols.slice(0, 50).map((s) => (
                <button
                  key={s.symbol}
                  className={`symbol-item ${s.symbol === selected ? "active" : ""}`}
                  onClick={() => {
                    onChange(s.symbol);
                    setIsOpen(false);
                    setSearch("");
                  }}
                >
                  <span className="symbol-base">{s.base}</span>
                  <span className="symbol-quote">/{s.quote}</span>
                </button>
              ))
            )}
          </div>
        </div>
      )}

      <style jsx>{`
        .symbol-selector {
          position: relative;
        }

        .selector-trigger {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: #12121a;
          border: 1px solid #1a1a2e;
          border-radius: 8px;
          color: #ffffff;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .selector-trigger:hover {
          border-color: #6366f1;
        }

        .chevron {
          width: 16px;
          height: 16px;
          color: #a0a0b0;
          transition: transform 0.2s ease;
        }

        .chevron.open {
          transform: rotate(180deg);
        }

        .dropdown {
          position: absolute;
          top: calc(100% + 8px);
          left: 0;
          width: 240px;
          background: #12121a;
          border: 1px solid #1a1a2e;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
          z-index: 100;
        }

        .search-input {
          width: 100%;
          padding: 12px 16px;
          background: #0a0a0f;
          border: none;
          border-bottom: 1px solid #1a1a2e;
          color: #ffffff;
          font-size: 14px;
          outline: none;
        }

        .search-input::placeholder {
          color: #606070;
        }

        .symbol-list {
          max-height: 300px;
          overflow-y: auto;
        }

        .symbol-item {
          display: flex;
          align-items: center;
          width: 100%;
          padding: 12px 16px;
          background: transparent;
          border: none;
          color: #ffffff;
          font-size: 14px;
          cursor: pointer;
          transition: background 0.15s ease;
          text-align: left;
        }

        .symbol-item:hover {
          background: #1a1a2e;
        }

        .symbol-item.active {
          background: linear-gradient(90deg, rgba(99, 102, 241, 0.2) 0%, transparent 100%);
          border-left: 3px solid #6366f1;
        }

        .symbol-base {
          font-weight: 600;
        }

        .symbol-quote {
          color: #606070;
        }

        .loading {
          padding: 20px;
          text-align: center;
          color: #606070;
        }
      `}</style>
    </div>
  );
}

export const SymbolSelector = memo(SymbolSelectorComponent);
