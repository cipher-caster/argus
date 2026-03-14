"use client";

import { Sparkline } from "@/components/features/chart/Sparkline";
import { Skeleton } from "@/components/ui/skeleton";
import { generateDeterministicSparkline } from "@/lib/chartUtils";
import { formatChange, formatPrice } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Bitcoin } from "lucide-react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Reuses the same cache key as DashboardWatchlist — no duplicate fetch
function useBTCTicker() {
  return useQuery({
    queryKey: ["market-tickers"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/market/tickers`);
      if (!res.ok) throw new Error("Failed to fetch tickers");
      const data = await res.json();
      const map: Record<string, { price: number; change_24h: number }> = {};
      data.tickers?.forEach((t: any) => { map[t.symbol] = t; });
      return map;
    },
    staleTime: 15_000,
    refetchInterval: 30_000,
    gcTime: 5 * 60_000,
    placeholderData: keepPreviousData,
  });
}

export function BTCCard() {
  const { data: tickers, isLoading } = useBTCTicker();
  const btc = tickers?.["BTC/USDT"] as any;

  if (isLoading && !btc) {
    return (
      <div className="bg-secondary/30 border border-border/50 rounded-2xl p-4 space-y-3">
        <Skeleton className="w-20 h-3" />
        <Skeleton className="w-32 h-7" />
        <Skeleton className="w-full h-10" />
        <div className="flex justify-between">
          <Skeleton className="w-20 h-3" />
          <Skeleton className="w-20 h-3" />
        </div>
      </div>
    );
  }

  const price = btc?.price ?? 0;
  const change = btc?.change_24h ?? 0;
  const high = btc?.high_24h ?? 0;
  const low = btc?.low_24h ?? 0;
  const isUp = change >= 0;

  const sparkline = btc?.sparkline_in_7d?.length > 0
    ? btc.sparkline_in_7d
    : generateDeterministicSparkline("BTC/USDT", price, change);

  return (
    <Link href="/chart/BTC-USDT" className="block group">
      <div className="bg-secondary/30 border border-border/50 rounded-2xl p-4 hover:border-primary/30 hover:bg-secondary/50 transition-all duration-300 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            <Bitcoin size={11} className="text-[#f59e0b]" />
            BTC / USDT
          </div>
          <span className={cn("text-[11px] font-black font-mono", isUp ? "text-success" : "text-danger")}>
            {formatChange(change)}
          </span>
        </div>

        <div className="text-2xl font-black font-mono tracking-tight group-hover:text-primary transition-colors">
          ${price > 0 ? formatPrice(price) : "—"}
        </div>

        <div className="h-10">
          <Sparkline data={sparkline} height={40} />
        </div>

        <div className="flex justify-between text-[10px] font-mono text-muted-foreground">
          <span>H: <span className="text-success">${high > 0 ? formatPrice(high) : "—"}</span></span>
          <span>L: <span className="text-danger">${low > 0 ? formatPrice(low) : "—"}</span></span>
        </div>
      </div>
    </Link>
  );
}
