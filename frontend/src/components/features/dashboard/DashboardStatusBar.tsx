"use client";

import { useOracleSignalSummary } from "@/hooks/useAnalyticsData";
import { useMarketIndicators } from "@/hooks/useMarketIndicators";
import { formatVolume } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { RefreshCcw, Zap } from "lucide-react";
import { useState } from "react";

function Divider() {
  return <div className="h-4 w-px bg-border/50 shrink-0" />;
}

export function DashboardStatusBar() {
  const { data: oracle, isLoading: oracleLoading, refetch: refetchOracle, isRefetching } = useOracleSignalSummary();
  const { data: indicators } = useMarketIndicators();
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refetchOracle();
    setRefreshing(false);
  };

  // Oracle visuals
  const marketState = oracle?.market_state ?? "—";
  const stateColor =
    marketState === "STRONG BULL" ? "text-green-600 dark:text-green-400" :
    marketState === "STRONG BEAR" ? "text-red-600 dark:text-red-400" :
    marketState === "SLEEPING" ? "text-blue-600 dark:text-blue-400" :
    "text-cyan-600 dark:text-cyan-400";
  const bgColor =
    marketState === "STRONG BULL" ? "bg-green-500/5 border-green-500/20" :
    marketState === "STRONG BEAR" ? "bg-red-500/5 border-red-500/20" :
    marketState === "SLEEPING" ? "bg-blue-500/5 border-blue-500/20" :
    "bg-secondary/30 border-border/50";

  // Parse top signals
  const longs: string[] = [];
  const shorts: string[] = [];
  oracle?.top_signals?.slice(0, 4).forEach((sig: string) => {
    const parts = sig.split(" ");
    const ticker = parts[0].replace("/USDT", "");
    const score = parts[1] ?? "";
    if (score.startsWith("-")) shorts.push(ticker);
    else longs.push(ticker);
  });

  // Market indicators
  const rsi = indicators?.average_rsi?.value;
  const rsiStatus = rsi !== undefined ? (rsi > 70 ? "OB" : rsi < 30 ? "OS" : "Neutral") : null;
  const rsiColor = rsi !== undefined ? (rsi > 70 ? "text-red-600 dark:text-red-400" : rsi < 30 ? "text-green-600 dark:text-green-400" : "text-muted-foreground") : "text-muted-foreground";

  const cap = indicators?.total_market_cap?.value;
  const capRegime = indicators?.total_market_cap?.regime;
  const capColor = capRegime === "BULLISH" ? "text-green-600 dark:text-green-400" : capRegime === "BEARISH" ? "text-red-600 dark:text-red-400" : "text-muted-foreground";

  const dom = indicators?.btc_dominance?.value;
  const domStatus = dom !== undefined ? (dom > 55 ? "Heavy" : dom < 45 ? "Alt Season" : "Balanced") : null;
  const domColor = dom !== undefined ? (dom > 55 ? "text-yellow-600 dark:text-yellow-400" : dom < 45 ? "text-purple-600 dark:text-purple-400" : "text-muted-foreground") : "text-muted-foreground";

  if (oracleLoading && !oracle) {
    return <div className="h-10 rounded-xl bg-secondary/30 border border-border/50 animate-pulse" />;
  }

  return (
    <div className={cn("flex items-center gap-3 px-4 h-10 rounded-xl border text-xs font-bold overflow-x-auto scrollbar-none", bgColor)}>
      {/* Oracle state */}
      <div className="flex items-center gap-1.5 shrink-0">
        <Zap size={11} className={stateColor} />
        <span className={cn("font-black uppercase tracking-wide", stateColor)}>{marketState}</span>
      </div>

      {oracle && (
        <>
          <span className="text-muted-foreground/50 text-xs shrink-0">
            <span className="text-green-500">{oracle.bullish_pct}%↑</span>
            {" / "}
            <span className="text-red-500">{oracle.bearish_pct}%↓</span>
          </span>

          {(longs.length > 0 || shorts.length > 0) && (
            <>
              <Divider />
              <div className="flex items-center gap-2 shrink-0">
                {longs.length > 0 && (
                  <div className="flex items-center gap-1">
                    <span className="text-[9px] text-green-500 uppercase">L:</span>
                    {longs.slice(0, 2).map((t) => (
                      <span key={t} className="bg-background border border-green-500/30 px-1 py-px rounded text-[9px] text-green-500">{t}</span>
                    ))}
                  </div>
                )}
                {shorts.length > 0 && (
                  <div className="flex items-center gap-1">
                    <span className="text-[9px] text-red-500 uppercase">S:</span>
                    {shorts.slice(0, 2).map((t) => (
                      <span key={t} className="bg-background border border-red-500/30 px-1 py-px rounded text-[9px] text-red-500">{t}</span>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </>
      )}

      {/* Market Indicators */}
      {rsi !== undefined && (
        <>
          <Divider />
          <span className="shrink-0 text-muted-foreground">
            RSI <span className={cn("font-black", rsiColor)}>{rsi.toFixed(1)}</span>
            <span className={cn("ml-1 text-[9px]", rsiColor)}>{rsiStatus}</span>
          </span>
        </>
      )}

      {cap !== undefined && (
        <>
          <Divider />
          <span className="shrink-0 text-muted-foreground">
            MCap <span className={cn("font-black", capColor)}>{formatVolume(cap)}</span>
          </span>
        </>
      )}

      {dom !== undefined && (
        <>
          <Divider />
          <span className="shrink-0 text-muted-foreground">
            BTC Dom <span className={cn("font-black", domColor)}>{dom.toFixed(1)}%</span>
            <span className={cn("ml-1 text-[9px]", domColor)}>{domStatus}</span>
          </span>
        </>
      )}

      {/* Refresh */}
      <button
        onClick={handleRefresh}
        disabled={refreshing || isRefetching}
        className="ml-auto shrink-0 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40"
        title="Refresh"
      >
        <RefreshCcw size={12} className={cn((refreshing || isRefetching) && "animate-spin")} />
      </button>
    </div>
  );
}
