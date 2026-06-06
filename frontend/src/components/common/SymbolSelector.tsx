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

import { cn } from "@/lib/utils";
import { ChevronDown, Search } from "lucide-react";

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
    <div className="relative">
      <button className={cn("flex items-center gap-3 px-4 py-2.5 bg-secondary border border-border rounded-xl transition-all duration-200", "hover:border-primary/50 hover:shadow-lg active:scale-95")} onClick={() => setIsOpen(!isOpen)}>
        <span className="text-sm font-bold tracking-tight">{selectedSymbol?.base || "BTC"}/USDT</span>
        <ChevronDown size={16} className={cn("text-muted-foreground transition-transform duration-200", isOpen ? "rotate-180" : "rotate-0")} />
      </button>

      {isOpen && (
        <div className="absolute top-[calc(100%+8px)] left-0 w-[280px] bg-card border border-border rounded-2xl shadow-2xl overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-200">
          <div className="relative">
            <Search size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              className="w-full pl-10 pr-4 py-3 bg-muted/30 border-b border-border text-sm outline-none focus:bg-muted/50 transition-colors"
              placeholder="Search coins..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
          </div>

          <div className="max-height-[400px] overflow-y-auto py-1">
            {isLoading ? (
              <div className="p-8 text-center text-sm text-muted-foreground italic flex flex-col items-center gap-2">
                <div className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
                Loading symbols...
              </div>
            ) : (
              filteredSymbols.slice(0, 50).map((s) => (
                <button
                  key={s.symbol}
                  className={cn("flex items-center w-full px-4 py-2.5 text-sm transition-all text-left", s.symbol === selected ? "bg-primary/10 border-l-[3px] border-primary" : "bg-transparent hover:bg-muted/50 border-l-[3px] border-transparent")}
                  onClick={() => {
                    onChange(s.symbol);
                    setIsOpen(false);
                    setSearch("");
                  }}
                >
                  <span className="font-bold">{s.base}</span>
                  <span className="text-muted-foreground">/{s.quote}</span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export const SymbolSelector = memo(SymbolSelectorComponent);
