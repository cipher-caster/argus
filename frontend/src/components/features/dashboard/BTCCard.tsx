"use client";

import { Sparkline } from "@/components/features/chart/Sparkline";
import { Skeleton } from "@/components/ui/skeleton";
import { generateDeterministicSparkline } from "@/lib/chartUtils";
import { formatChange, formatPrice } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { useTickers } from "@/hooks/useMarketData";
import { Bitcoin } from "lucide-react";
import Link from "next/link";

export function BTCCard() {
  const { data: tickersResponse, isLoading } = useTickers();
  
  // Find BTC ticker instead of casting map index to any
  const btc = tickersResponse?.tickers?.find(t => t.symbol === "BTC/USDT");

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

  // BTCCard relies on sparkline_in_7d if present, else generates one
  const sparkData = btc?.sparkline_in_7d;
  const sparkline = sparkData && sparkData.length > 0
    ? sparkData
    : generateDeterministicSparkline("BTC/USDT", price, change);

  return (
    <Link href="/chart/BTC-USDT" className="block group">
      <div className="bg-secondary/30 border border-border/50 rounded-2xl p-4 hover:border-primary/30 hover:bg-secondary/50 transition-all duration-300 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            <Bitcoin size={11} className="text-[#f59e0b]" />
            BTC / USDT
          </div>
          <span className={cn("text-[11px] font-medium font-mono", isUp ? "text-success" : "text-danger")}>
            {formatChange(change)}
          </span>
        </div>

        <div className="text-2xl font-medium font-mono tracking-tight group-hover:text-primary transition-colors">
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
