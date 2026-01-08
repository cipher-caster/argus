"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { TrendingDown, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";

interface CoinDetailsPanelProps {
  symbol: string;
}

interface TickerDetails {
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
  high_24h: number;
  low_24h: number;
}

function formatVolume(volume: number): string {
  if (!volume) return "—";
  if (volume >= 1_000_000_000) return `$${(volume / 1_000_000_000).toFixed(2)}B`;
  if (volume >= 1_000_000) return `$${(volume / 1_000_000).toFixed(2)}M`;
  if (volume >= 1_000) return `$${(volume / 1_000).toFixed(2)}K`;
  return `$${volume.toFixed(2)}`;
}

export function CoinDetailsPanel({ symbol }: CoinDetailsPanelProps) {
  const [details, setDetails] = useState<TickerDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    async function fetchDetails() {
      try {
        setLoading(true);
        const res = await fetch(`${apiUrl}/api/market/tickers`);
        if (!res.ok) return;
        const data = await res.json();
        const ticker = data.tickers?.find((t: TickerDetails) => t.symbol === symbol);
        if (ticker) {
          setDetails(ticker);
        }
      } catch (e) {
        console.error("Failed to fetch coin details", e);
      } finally {
        setLoading(false);
      }
    }

    fetchDetails();
    const interval = setInterval(fetchDetails, 10000);
    return () => clearInterval(interval);
  }, [symbol]);

  if (loading && !details) {
    return (
      <div className="p-4 flex flex-col gap-4 border-t border-border bg-secondary shrink-0 overflow-y-auto">
        {/* Header Skeleton */}
        <div className="flex gap-2">
          <Skeleton className="h-6 w-20" />
          <Skeleton className="h-4 w-12" />
        </div>

        {/* Price Skeleton */}
        <div className="flex gap-3">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-6 w-16" />
        </div>

        {/* Stats Skeleton */}
        <div className="flex flex-col gap-2 mt-2">
          <Skeleton className="h-3 w-24 mb-1" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
        </div>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="p-4 flex flex-col gap-4 border-t border-border bg-secondary shrink-0 overflow-y-auto">
        <div className="p-6 text-center text-muted-foreground text-[12px]">No data available</div>
      </div>
    );
  }

  const isPositive = (details.change_24h || 0) >= 0;
  const priceRange = details.high_24h - details.low_24h;
  const currentPosition = priceRange > 0 ? ((details.price - details.low_24h) / priceRange) * 100 : 50;

  return (
    <div className="p-4 flex flex-col gap-4 border-t border-border bg-secondary shrink-0 overflow-y-auto scrollbar-thin scrollbar-thumb-muted">
      {/* Header */}
      <div className="flex items-baseline gap-2">
        <div className="text-[18px] font-bold text-foreground">{symbol.replace("/USDT", "")}</div>
        <div className="text-[12px] text-muted-foreground font-medium">{symbol}</div>
      </div>

      {/* Price */}
      <div className="flex items-baseline gap-3">
        <div className="text-[24px] font-extrabold text-foreground tracking-tighter">${details.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}</div>
        <div className={cn("flex items-center gap-1 text-[14px] font-bold px-2 py-1 rounded-md", isPositive ? "text-success bg-success/15" : "text-danger bg-danger/15")}>
          {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          <span>
            {isPositive ? "+" : ""}
            {details.change_24h?.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Key Stats */}
      <div className="flex flex-col gap-2">
        <div className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Key Stats (24H)</div>

        {[
          { label: "Volume", value: formatVolume(details.volume_24h) },
          { label: "High", value: `$${details.high_24h?.toLocaleString(undefined, { maximumFractionDigits: 6 })}` },
          { label: "Low", value: `$${details.low_24h?.toLocaleString(undefined, { maximumFractionDigits: 6 })}` },
          { label: "Range", value: `$${priceRange.toLocaleString(undefined, { maximumFractionDigits: 6 })}` },
        ].map((stat) => (
          <div key={stat.label} className="flex justify-between items-center py-0.5">
            <span className="text-[13px] text-muted-foreground font-medium">{stat.label}</span>
            <span className="text-[13px] font-bold text-foreground font-mono">{stat.value}</span>
          </div>
        ))}
      </div>

      {/* Price Position Bar */}
      <div className="flex flex-col gap-2 mt-1">
        <div className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-1">24H Price Position</div>
        <div className="h-1.5 w-full bg-muted rounded-full relative overflow-visible">
          <div className="h-full bg-gradient-to-r from-danger to-success rounded-full" />
          <div className="absolute top-1/2 w-3 h-3 bg-foreground border-2 border-secondary rounded-full -translate-y-1/2 -translate-x-1/2 transition-all duration-500 shadow-sm" style={{ left: `${currentPosition}%` }} />
        </div>
        <div className="flex justify-between text-[11px] font-bold text-muted-foreground font-mono">
          <span>${details.low_24h?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
          <span>${details.high_24h?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
        </div>
      </div>

      {/* Performance */}
      <div className="flex flex-col gap-2 mt-1">
        <div className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Performance</div>
        <div className="grid grid-cols-1 gap-2">
          <div className={cn("p-3 rounded-xl text-center border transition-all", isPositive ? "bg-success/5 border-success/20" : "bg-danger/5 border-danger/20")}>
            <div className={cn("text-[16px] font-extrabold font-mono", isPositive ? "text-success" : "text-danger")}>
              {isPositive ? "+" : ""}
              {details.change_24h?.toFixed(2)}%
            </div>
            <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mt-0.5">24 Hour Change</div>
          </div>
        </div>
      </div>
    </div>
  );
}
