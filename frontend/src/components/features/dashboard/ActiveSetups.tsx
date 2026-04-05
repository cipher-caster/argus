"use client";

import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { DirectionBadge } from "@/components/ui/DirectionBadge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useBestSetups } from "@/hooks/useAnalyticsData";
import { CoinMeta, useCoinMeta } from "@/hooks/useCoinMeta";
import { BestSetupItem } from "@/lib/api";
import { formatPriceCompact, formatPercentageChange } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { ChevronRight, TrendingDown, TrendingUp, Zap } from "lucide-react";
import Link from "next/link";

function SetupRow({ item, coinMeta }: { item: BestSetupItem; coinMeta: Map<string, CoinMeta> }) {
  const isLong = item.direction === "LONG";
  const tpPct = isLong ? formatPercentageChange(item.entry, item.tp) : formatPercentageChange(item.tp, item.entry, "SHORT");
  const isWithTrend = item.reason.startsWith("(trend)");

  // Strip the regime tag prefix from reason text
  let reason = item.reason.replace(/^\(trend\)\s*/, "").replace(/^\(counter\)\s*/, "");

  return (
    <Link href={`/chart/${item.symbol.replace("/", "-")}`} className="block group">
      <div className="flex items-center gap-3 px-4 py-3.5 hover:bg-muted/50 transition-colors">
        <CoinIcon symbol={item.symbol} coinMeta={coinMeta} size={32} />

        {/* Symbol + reason */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-black text-sm group-hover:text-primary transition-colors">
              {item.symbol.replace("/USDT", "").replace("USDT", "")}
            </span>
            <DirectionBadge direction={item.direction} />
            {isWithTrend && (
              <span className="text-[8px] font-bold px-1 py-0.5 rounded bg-primary/10 text-primary">TREND</span>
            )}
          </div>
          <p className="text-[10px] text-muted-foreground truncate mt-0.5">
            {reason.length > 55 ? reason.slice(0, 55) + "…" : reason}
          </p>
        </div>

        {/* Entry / TP / SL */}
        <div className="shrink-0 w-[140px] text-right">
          <div className="text-xs font-mono font-medium">${formatPriceCompact(item.entry)}</div>
          <div className="flex gap-2 mt-0.5 justify-end">
            <span className="text-[9px] font-mono text-green-600 dark:text-green-400">TP ${formatPriceCompact(item.tp)}</span>
            <span className="text-[9px] font-mono text-red-600 dark:text-red-400">SL ${formatPriceCompact(item.sl)}</span>
          </div>
        </div>

        {/* Conviction */}
        <div className="shrink-0 w-14">
          <div className="flex justify-between text-[9px] mb-1">
            <span className="text-muted-foreground">Conv.</span>
            <span className={cn("font-bold", item.conviction >= 80 ? "text-green-600 dark:text-green-400" : item.conviction >= 65 ? "text-yellow-600 dark:text-yellow-400" : "text-muted-foreground")}>
              {item.conviction}%
            </span>
          </div>
          <div className="h-1 bg-muted/40 rounded-full overflow-hidden">
            <div
              className={cn("h-full rounded-full transition-all", item.conviction >= 80 ? "bg-green-500" : item.conviction >= 65 ? "bg-yellow-500" : "bg-primary/60")}
              style={{ width: `${item.conviction}%` }}
            />
          </div>
        </div>
      </div>
    </Link>
  );
}

export function ActiveSetups() {
  const { coinMeta } = useCoinMeta();
  const { data, isLoading } = useBestSetups("4h");
  const items = (data?.data ?? []).slice(0, 5);

  return (
    <div className="bg-secondary/30 border border-border/50 rounded-2xl overflow-hidden h-full">
      <div className="flex items-center justify-between px-4 py-3.5 border-b border-border/30">
        <div className="flex items-center gap-2">
          <Zap size={14} className="text-primary" />
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="text-xs font-black uppercase tracking-widest cursor-help">Best Setups</span>
              </TooltipTrigger>
              <TooltipContent side="bottom" align="start" className="max-w-[240px] text-xs">
                Titan signals filtered by market regime. BULL → longs prioritized. BEAR → shorts prioritized.
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          {!isLoading && items.length > 0 && (
            <span className="bg-primary/20 text-primary text-[10px] font-bold px-1.5 py-0.5 rounded-md">{items.length}</span>
          )}
        </div>
        <Link href="/analytics" className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors font-bold">
          Analytics <ChevronRight size={10} />
        </Link>
      </div>

      <div className="divide-y divide-border/20">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3.5">
              <Skeleton className="w-8 h-8 rounded-full shrink-0" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="w-24 h-3" />
                <Skeleton className="w-48 h-2.5" />
              </div>
              <div className="space-y-1 mr-3">
                <Skeleton className="w-16 h-3" />
                <Skeleton className="w-12 h-2.5" />
              </div>
              <Skeleton className="w-14 h-5 rounded-full" />
            </div>
          ))
        ) : items.length === 0 ? (
          <div className="py-12 text-center px-4">
            <p className="text-sm font-black text-muted-foreground/50 uppercase tracking-widest">No setups right now</p>
            <p className="text-[11px] text-muted-foreground/40 mt-1.5 max-w-[200px] mx-auto">No high-conviction Titan signals matching the current regime</p>
            <Link href="/analytics" className="inline-block mt-4 text-[11px] font-bold text-primary hover:text-primary/80 transition-colors">
              Check other timeframes →
            </Link>
          </div>
        ) : (
          items.map((item) => <SetupRow key={item.symbol} item={item} coinMeta={coinMeta} />)
        )}
      </div>
    </div>
  );
}
