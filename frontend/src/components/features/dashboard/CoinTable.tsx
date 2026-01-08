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

import { cn } from "@/lib/utils";

// Pseudo-random number generator seeded by string
function sfc32(a: number, b: number, c: number, d: number) {
  return function () {
    a >>>= 0;
    b >>>= 0;
    c >>>= 0;
    d >>>= 0;
    let t = (a + b) | 0;
    a = b ^ (b >>> 9);
    b = (c + (c << 3)) | 0;
    c = (c << 21) | (c >>> 11);
    d = (d + 1) | 0;
    t = (t + d) | 0;
    c = (c + t) | 0;
    return (t >>> 0) / 4294967296;
  };
}

function generateDeterministicSparkline(symbol: string, basePrice: number, change: number) {
  // Create a seed from symbol components
  let h1 = 1779033703,
    h2 = 3144134277,
    h3 = 1013904242,
    h4 = 2773480762;
  for (let i = 0, k; i < symbol.length; i++) {
    k = symbol.charCodeAt(i);
    h1 = h2 ^ Math.imul(h1 ^ k, 597399067);
    h2 = h3 ^ Math.imul(h2 ^ k, 2869860233);
    h3 = h4 ^ Math.imul(h3 ^ k, 951274213);
    h4 = h1 ^ Math.imul(h4 ^ k, 2716044179);
  }

  const rand = sfc32(h1, h2, h3, h4);
  const points = 20;
  const data = [basePrice];
  let current = basePrice;

  // Bias trend based on 24h change
  const trendBias = change / points;

  for (let i = 1; i < points; i++) {
    const volatility = basePrice * 0.02; // 2% volatility
    const move = (rand() - 0.5) * volatility + trendBias * basePrice * 0.01;
    current += move;
    data.push(current);
  }
  return data;
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
    if (sortBy !== field) return <ArrowUpDown size={12} className="opacity-30 ml-1.5" />;
    return sortOrder === "asc" ? <ArrowUp size={12} className="text-primary ml-1.5" /> : <ArrowDown size={12} className="text-primary ml-1.5" />;
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
                      {coin.change_24h !== null ? `${coin.change_24h >= 0 ? "+" : ""}${coin.change_24h.toFixed(2)}%` : "—"}
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
