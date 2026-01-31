"use client";

import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { useToast } from "@/components/ui/toaster";
import { useOracleSignalSummary } from "@/hooks/useAnalyticsData";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { cn } from "@/lib/utils";
import { RefreshCcw, Zap } from "lucide-react";
import Link from "next/link";

export function OracleSignalSummary() {
  const { data, isLoading, error, refetch, isRefetching } = useOracleSignalSummary();
  const { toast, dismiss } = useToast();

  const handleRefresh = async () => {
    const id = toast("Refreshing Oracle signals...", "info");
    await refetch();
    dismiss(id);
    toast("Oracle signals refreshed", "success");
  };

  if (isLoading) return <div className="h-12 bg-secondary/20 animate-pulse rounded-lg" />;
  if (error) return <div className="h-12 flex items-center justify-center bg-secondary/30 border border-red-500/20 text-red-500 rounded-lg italic text-xs px-4">Oracle Unavailable</div>;

  const confidence = Math.max(data?.bullish_pct || 0, data?.bearish_pct || 0);
  const marketState = data?.market_state || "Analyzing";

  // Label color based on market state
  const labelColorClass = marketState === "STRONG BULL" ? "text-green-400" : marketState === "STRONG BEAR" ? "text-red-400" : "text-cyan-400";
  const bgClass = marketState === "STRONG BULL" ? "bg-green-500/10" : marketState === "STRONG BEAR" ? "bg-red-500/10" : "bg-cyan-500/10";

  return (
    <div className={cn("bg-secondary/30 rounded-lg px-4 py-3 border border-border/50 backdrop-blur-sm flex items-center justify-between gap-4", bgClass)}>
      {/* Left: Icon + Label */}
      <div className="flex items-center gap-3">
        <Zap size={18} className="text-primary" />
        <div className="flex items-center gap-3">
          <div>
            <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-wide">Oracle Intelligence</div>
            <div className={cn("text-sm font-black uppercase tracking-tight", labelColorClass)}>{marketState}</div>
          </div>
        </div>
      </div>

      {/* Center: Metrics */}
      <div className="flex items-center gap-4">
        <div className="text-center">
          <div className={cn("text-xl font-black", labelColorClass)}>{confidence}%</div>
          <div className="text-[9px] text-muted-foreground uppercase tracking-wider">Confidence</div>
        </div>
        <div className="h-8 w-px bg-border/50" />
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase">
          <span className="text-green-500">{data?.bullish_pct || 0}% Bull</span>
          <span className="text-muted-foreground">/</span>
          <span className="text-red-500">{data?.bearish_pct || 0}% Bear</span>
        </div>
      </div>

      {/* Right: Top Signals */}
      <div className="flex items-center gap-3">
        {(() => {
          const longs: string[] = [];
          const shorts: string[] = [];

          data?.top_signals?.slice(0, 4).forEach((sig: string) => {
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
            <div className="flex items-center gap-2">
              {longs.length > 0 && (
                <div className="flex items-center gap-1">
                  <span className="text-[9px] text-green-500 font-bold uppercase">L:</span>
                  {longs.slice(0, 2).map((ticker) => (
                    <span key={ticker} className="bg-background border border-green-500/30 px-1.5 py-0.5 rounded text-[9px] font-bold text-green-500">
                      {ticker}
                    </span>
                  ))}
                </div>
              )}
              {shorts.length > 0 && (
                <div className="flex items-center gap-1">
                  <span className="text-[9px] text-red-500 font-bold uppercase">S:</span>
                  {shorts.slice(0, 2).map((ticker) => (
                    <span key={ticker} className="bg-background border border-red-500/30 px-1.5 py-0.5 rounded text-[9px] font-bold text-red-500">
                      {ticker}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })()}
        <button onClick={handleRefresh} disabled={isRefetching} className="p-1.5 rounded-md text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50" title="Refresh">
          <RefreshCcw size={14} className={cn(isRefetching && "animate-spin")} />
        </button>
      </div>
    </div>
  );
}

function CoinBadge({ ticker }: { ticker: string }) {
  const { coinMeta } = useCoinMeta();
  return (
    <Link href={`/chart/${ticker}-USDT`} className="flex items-center gap-1 bg-background border border-border px-1.5 py-0.5 rounded-md hover:border-primary/50 hover:bg-muted transition-all group">
      <CoinIcon symbol={`${ticker}/USDT`} coinMeta={coinMeta} size={14} />
      <span className="text-[10px] font-bold group-hover:text-primary transition-colors">{ticker}</span>
    </Link>
  );
}
