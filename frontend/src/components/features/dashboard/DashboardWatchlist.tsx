"use client";

import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useOracleScreener } from "@/hooks/useAnalyticsData";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { formatChange, formatPrice } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { useWatchlistStore } from "@/stores/watchlistStore";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Plus, Star } from "lucide-react";
import Link from "next/link";
import { useMemo } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function useWatchlistTickers() {
  return useQuery({
    queryKey: ["market-tickers"],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/market/tickers`);
      if (!res.ok) throw new Error("Failed to fetch tickers");
      const data = await res.json();
      const map: Record<string, { price: number; change_24h: number }> = {};
      data.tickers?.forEach((t: any) => {
        map[t.symbol] = { price: t.price, change_24h: t.change_24h };
      });
      return map;
    },
    staleTime: 15_000,
    refetchInterval: 30_000,
    gcTime: 5 * 60_000,
    placeholderData: keepPreviousData,
  });
}

function ScoreChip({ score }: { score: number | null }) {
  if (score === null) return <span className="text-muted-foreground/30 text-[10px] font-mono w-7 text-center block">—</span>;

  const colorClass =
    score >= 3 ? "bg-green-500/20 text-green-700 dark:text-green-400 border-green-500/30" :
    score >= 1 ? "bg-green-500/10 text-green-600/70 dark:text-green-500/70 border-green-500/20" :
    score <= -3 ? "bg-red-500/20 text-red-700 dark:text-red-400 border-red-500/30" :
    score <= -1 ? "bg-red-500/10 text-red-600/70 dark:text-red-500/70 border-red-500/20" :
    "bg-muted/40 text-muted-foreground border-border/30";

  const label = score > 0 ? `+${score}` : `${score}`;

  return (
    <span className={cn("inline-flex items-center justify-center w-9 px-1.5 py-0.5 rounded border text-[10px] font-black font-mono", colorClass)}>
      {label}
    </span>
  );
}

export function DashboardWatchlist() {
  const { items } = useWatchlistStore();
  const { coinMeta } = useCoinMeta();
  const { data: tickers, isLoading: tickersLoading } = useWatchlistTickers();
  const { data: screener } = useOracleScreener("1h", 50);

  const scoreMap = useMemo(() => {
    const map: Record<string, number> = {};
    screener?.data?.forEach((s) => { map[s.symbol] = s.score; });
    return map;
  }, [screener]);

  return (
    <div className="bg-secondary/30 border border-border/50 rounded-2xl overflow-hidden h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3.5 border-b border-border/30">
        <div className="flex items-center gap-2">
          <Star size={14} className="text-[#f59e0b] fill-[#f59e0b]" />
          <span className="text-xs font-black uppercase tracking-widest">Watchlist</span>
          {items.length > 0 && (
            <span className="bg-muted text-muted-foreground text-[10px] font-bold px-1.5 py-0.5 rounded-md">{items.length}</span>
          )}
        </div>
        <div className="flex items-center gap-2 text-[9px] font-bold uppercase tracking-widest text-muted-foreground/50">
          <span className="w-9 text-center">Score</span>
        </div>
      </div>

      {/* Items */}
      <div className="divide-y divide-border/20">
        {items.length === 0 ? (
          <div className="py-12 text-center px-4">
            <Star size={20} className="opacity-10 mx-auto mb-3" />
            <p className="text-xs text-muted-foreground/50 mb-3">Star coins from the market table to track them here</p>
            <Link href="/markets/gainers" className="inline-flex items-center gap-1 text-[11px] font-bold text-primary hover:text-primary/80 transition-colors">
              <Plus size={11} /> Browse markets
            </Link>
          </div>
        ) : (
          items.map((item) => {
            const ticker = tickers?.[item.symbol];
            const normalizedSymbol = item.symbol.replace("/", "");
            const score = scoreMap[normalizedSymbol] ?? null;

            return (
              <Link
                key={item.symbol}
                href={`/chart/${item.symbol.replace("/", "-")}`}
                className="flex items-center gap-3 px-4 py-3 hover:bg-muted/50 transition-colors group"
              >
                <CoinIcon symbol={item.symbol} coinMeta={coinMeta} size={28} />
                <div className="flex-1 min-w-0">
                  <span className="font-bold text-sm group-hover:text-primary transition-colors">
                    {item.symbol.replace("/USDT", "")}
                  </span>
                </div>

                <div className="text-right shrink-0 mr-1">
                  {tickersLoading && !ticker ? (
                    <div className="space-y-1">
                      <Skeleton className="w-14 h-3 ml-auto" />
                      <Skeleton className="w-10 h-2.5 ml-auto" />
                    </div>
                  ) : ticker ? (
                    <>
                      <div className="text-xs font-mono font-semibold">${formatPrice(ticker.price)}</div>
                      <div className={cn("text-[10px] font-bold", ticker.change_24h >= 0 ? "text-success" : "text-danger")}>
                        {formatChange(ticker.change_24h)}
                      </div>
                    </>
                  ) : (
                    <span className="text-[10px] text-muted-foreground/40">—</span>
                  )}
                </div>

                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="shrink-0 cursor-default">
                        <ScoreChip score={score} />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent className="text-xs">
                      Oracle Score {score !== null ? `${score > 0 ? "+" : ""}${score}/4` : "not in top 50"}
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </Link>
            );
          })
        )}
      </div>
    </div>
  );
}
