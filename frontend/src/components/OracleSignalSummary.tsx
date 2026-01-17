"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useOracleSignalSummary } from "@/hooks/useAnalyticsData";
import { cn } from "@/lib/utils";
import { HelpCircle, Zap } from "lucide-react";

export function OracleSignalSummary() {
  const { data, isLoading, error } = useOracleSignalSummary();

  if (isLoading) return <Skeleton className="h-[180px] w-full rounded-xl" />;
  if (error) return <div className="h-full min-h-[200px] flex items-center justify-center bg-secondary border border-red-500/20 text-red-500 rounded-xl italic text-xs">Oracle Unavailable</div>;

  const confidence = Math.max(data?.bullish_pct || 0, data?.bearish_pct || 0);
  const marketState = data?.market_state || "Analyzing";

  // Label color based on market state
  const labelColorClass = marketState === "STRONG BULL" ? "text-green-400" : marketState === "STRONG BEAR" ? "text-red-400" : "text-cyan-400";

  return (
    <div className="bg-secondary border border-border rounded-xl p-4 h-full shadow-sm hover:shadow-lg transition-all duration-300 group min-h-[180px] flex flex-col">
      {/* Header - Matches IndicatorCard */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-primary">
            <Zap size={16} />
          </span>
          <span className="text-[13px] text-muted-foreground font-bold uppercase tracking-tight">Oracle Intelligence</span>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button className="p-1 rounded-md text-muted-foreground hover:text-foreground transition-colors">
                <HelpCircle size={14} />
              </button>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-[250px] text-center">
              <p>Confidence based on momentum scores across Top 50 Perpetual symbols.</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Value Display - Matches IndicatorCard */}
      <div className="flex items-baseline gap-2 mb-2">
        <span className={cn("text-3xl font-extrabold tracking-tighter leading-none", labelColorClass)}>{confidence}%</span>
        <span className={cn("text-sm font-semibold", labelColorClass)}>{marketState}</span>
      </div>
      <div className="text-xs text-muted-foreground">Confidence</div>

      {/* Footer Section - Pinned to bottom */}
      <div className="mt-auto flex flex-col gap-3">
        {/* Sentiment Bar */}
        <div className="space-y-1">
          <div className="flex justify-between text-[10px] font-bold uppercase tracking-wide">
            <span className="text-green-500">Bullish {data?.bullish_pct || 0}%</span>
            <span className="text-red-500">Bearish {data?.bearish_pct || 0}%</span>
          </div>
          <div className="h-2 w-full bg-muted/50 rounded-full overflow-hidden flex">
            <div className="h-full bg-green-500/80 transition-all duration-1000" style={{ width: `${data?.bullish_pct || 50}%` }} />
            <div className="h-full bg-red-500/80 transition-all duration-1000" style={{ width: `${data?.bearish_pct || 50}%` }} />
          </div>
        </div>

        {/* Alpha Signals - Without border to match card flow */}
        {/* Alpha Signals - Sorted by Long/Short */}
        <div className="pt-0 text-[11px] font-medium space-y-1.5">
          {(() => {
            const longs: string[] = [];
            const shorts: string[] = [];

            data?.top_signals?.forEach((sig: string) => {
              // Parse signal string (e.g., "BNB/USDT 4/4" or "ETH/USDT -3/4")
              const parts = sig.split(" ");
              const ticker = parts[0].replace("/USDT", "");
              const scorePart = parts[1] || "";

              if (scorePart.startsWith("-")) {
                shorts.push(ticker);
              } else {
                longs.push(ticker);
              }
            });

            return (
              <>
                {longs.length > 0 && (
                  <div className="flex items-start gap-1">
                    <span className="text-green-500 font-bold uppercase w-9 shrink-0">Long:</span>
                    <span className="text-muted-foreground leading-tight">{longs.join(", ")}</span>
                  </div>
                )}
                {shorts.length > 0 && (
                  <div className="flex items-start gap-1">
                    <span className="text-red-500 font-bold uppercase w-9 shrink-0">Short:</span>
                    <span className="text-muted-foreground leading-tight">{shorts.join(", ")}</span>
                  </div>
                )}
                {longs.length === 0 && shorts.length === 0 && <div className="text-[10px] text-muted-foreground italic">No active signals</div>}
              </>
            );
          })()}
        </div>
      </div>
    </div>
  );
}
