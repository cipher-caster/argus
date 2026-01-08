"use client";

/**
 * Coin Table Component
 * Professional CoinGlass-style table with rich data
 */

import { Sparkline } from "@/components/features/chart/Sparkline";
import { Skeleton } from "@/components/ui/skeleton";
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

import { generateDeterministicSparkline } from "@/lib/chartUtils";
import { formatChange, formatPrice, formatVolume } from "@/lib/formatters";
import { cn } from "@/lib/utils";

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
    if (sortBy !== field) return <ArrowUpDown size={12} className="opacity-30 ml-1.5" />;
    return sortOrder === "asc" ? <ArrowUp size={12} className="text-primary ml-1.5" /> : <ArrowDown size={12} className="text-primary ml-1.5" />;
  };

  if (!mounted) return <div className="bg-secondary border border-border rounded-xl h-[400px]"></div>;

  return (
    <div className="bg-secondary border border-border rounded-xl overflow-hidden shadow-sm">
      <table className="w-full border-collapse">
        <thead className="bg-muted/50">
          <tr>
            <th className="w-8 pl-4 pr-0 py-3"></th>
            <th className="w-10 px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider text-center font-mono">#</th>
            <th className="px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider text-left cursor-pointer select-none hover:text-foreground transition-colors" onClick={() => onSort("symbol")}>
              <div className="flex items-center">
                Symbol <SortIcon field="symbol" />
              </div>
            </th>

            <th className="px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider text-right cursor-pointer select-none hover:text-foreground transition-colors" onClick={() => onSort("price")}>
              <div className="flex items-center justify-end">
                Price <SortIcon field="price" />
              </div>
            </th>
            <th className="px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider text-right">24h Change</th>
            <th className="px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider text-right cursor-pointer select-none hover:text-foreground transition-colors" onClick={() => onSort("volume_24h")}>
              <div className="flex items-center justify-end">
                Volume (24h) <SortIcon field="volume_24h" />
              </div>
            </th>
            <th className="px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider text-right cursor-pointer select-none hover:text-foreground transition-colors" onClick={() => onSort("market_cap")}>
              <div className="flex items-center justify-end">
                Market Cap <SortIcon field="market_cap" />
              </div>
            </th>
            <th className="px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider text-center w-24">Last 7 Days</th>
            <th className="px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider text-right">24h High</th>
            <th className="px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider text-right">24h Low</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/50">
          {isLoading ? (
            Array.from({ length: 15 }).map((_, i) => (
              <tr key={i} className="animate-pulse">
                <td className="px-4 py-4">
                  <Skeleton className="w-4 h-4 rounded" />
                </td>
                <td className="px-4 py-4">
                  <Skeleton className="w-4 h-4 rounded mx-auto" />
                </td>
                <td className="px-4 py-4">
                  <div className="flex items-center gap-3">
                    <Skeleton className="w-7 h-7 rounded-full" />
                    <Skeleton className="w-16 h-4 rounded" />
                  </div>
                </td>
                <td className="px-4 py-4">
                  <Skeleton className="w-20 h-4 rounded ml-auto" />
                </td>
                <td className="px-4 py-4">
                  <Skeleton className="w-16 h-6 rounded-md ml-auto" />
                </td>
                <td className="px-4 py-4">
                  <Skeleton className="w-16 h-4 rounded ml-auto" />
                </td>
                <td className="px-4 py-4">
                  <Skeleton className="w-20 h-4 rounded ml-auto" />
                </td>
                <td className="px-4 py-4">
                  <Skeleton className="w-20 h-6 rounded mx-auto" />
                </td>
                <td className="px-4 py-4">
                  <Skeleton className="w-16 h-4 rounded ml-auto" />
                </td>
                <td className="px-4 py-4">
                  <Skeleton className="w-16 h-4 rounded ml-auto" />
                </td>
              </tr>
            ))
          ) : coins.length === 0 ? (
            <tr>
              <td colSpan={10} className="px-4 py-20 text-center">
                <div className="flex flex-col items-center gap-3 text-muted-foreground">
                  <Search size={32} className="opacity-20" />
                  <p className="text-sm">No coins found matching criteria</p>
                </div>
              </td>
            </tr>
          ) : (
            coins.map((coin) => {
              const isFav = favorites.includes(coin.symbol);
              return (
                <tr key={coin.symbol} className="group hover:bg-muted transition-colors cursor-pointer">
                  <td className="pl-4 pr-0 py-4 text-center">
                    <Star
                      size={14}
                      className={cn("cursor-pointer transition-all", isFav ? "text-[#f59e0b] fill-[#f59e0b]" : "text-muted-foreground hover:text-[#f59e0b]")}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavorite(coin.symbol);
                      }}
                    />
                  </td>
                  <td className="px-4 py-4 text-[13px] text-muted-foreground font-mono text-center">{coin.rank}</td>
                  <td className="px-4 py-4">
                    <Link href={`/chart/${coin.symbol.replace("/", "-")}`} className="flex items-center gap-3 no-underline text-inherit hover:no-underline">
                      <div className="w-7 h-7 rounded-full bg-primary text-white flex items-center justify-center text-[10px] font-extrabold shrink-0">{coin.name.slice(0, 1)}</div>
                      <span className="font-bold text-[14px] text-foreground tracking-tight">{coin.symbol}</span>
                    </Link>
                  </td>

                  <td className="px-4 py-4 text-right">
                    <span className="font-mono font-semibold text-[13px] text-foreground tracking-tight">${formatPrice(coin.price)}</span>
                  </td>
                  <td className="px-4 py-4 text-right">
                    <div className={cn("inline-flex items-center justify-center px-2 py-1 rounded-md text-[12px] font-bold min-w-[70px] font-mono", (coin.change_24h ?? 0) >= 0 ? "bg-success/15 text-success" : "bg-danger/15 text-danger")}>
                      {formatChange(coin.change_24h)}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right font-mono text-[13px] text-foreground tracking-tight">{formatVolume(coin.volume_24h)}</td>
                  <td className="px-4 py-4 text-right font-mono font-bold text-[13px] text-foreground tracking-tight">{formatVolume(coin.market_cap)}</td>
                  <td className="px-4 py-4 text-center">
                    <div className="inline-block">
                      <Sparkline data={generateDeterministicSparkline(coin.symbol, coin.price, coin.change_24h || 0)} width={80} height={24} />
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right text-muted-foreground text-[13px] font-mono">${formatPrice(coin.high_24h || 0)}</td>
                  <td className="px-4 py-4 text-right text-muted-foreground text-[13px] font-mono">${formatPrice(coin.low_24h || 0)}</td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

export const CoinTable = memo(CoinTableComponent);
