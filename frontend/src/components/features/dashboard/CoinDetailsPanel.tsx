"use client";

import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { Skeleton } from "@/components/ui/skeleton";
import { CoinAnalysisModal } from "@/components/features/chart/CoinAnalysisModal";
import { getCoinName, useCoinMeta } from "@/hooks/useCoinMeta";
import { formatChange, formatVolume } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { BarChart2, TrendingDown, TrendingUp, Zap } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CoinDetailsPanelProps {
  symbol: string;
  timeframe?: string;
}

interface CoinTicker {
  price: number;
  change_24h: number;
  volume_24h: number;
  high_24h: number;
  low_24h: number;
}

function useCoinTicker(symbol: string) {
  return useQuery<CoinTicker>({
    queryKey: ["ticker", symbol],
    queryFn: async () => {
      const url = new URL("/api/market/ticker", API_URL);
      url.searchParams.set("symbol", symbol);
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error("Failed to fetch ticker");
      return (await res.json()).data;
    },
    refetchInterval: 30_000,
    staleTime: 25_000,
    placeholderData: keepPreviousData,
  });
}

function useTitanDirect(symbol: string, timeframe: string) {
  return useQuery<any>({
    queryKey: ["titan-direct", symbol, timeframe],
    queryFn: async () => {
      const url = new URL(`/api/strategy/titan/${symbol}`, API_URL);
      url.searchParams.set("timeframe", timeframe);
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error("Failed to fetch Titan");
      return res.json();
    },
    refetchInterval: 60_000,
    staleTime: 50_000,
  });
}

export function CoinDetailsPanel({ symbol, timeframe = "4h" }: CoinDetailsPanelProps) {
  const { data: details, isLoading } = useCoinTicker(symbol);
  const { coinMeta } = useCoinMeta();
  const { data: titan, isLoading: titanLoading } = useTitanDirect(symbol, "4h");
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
  const [regime, setRegime] = useState<{ regime: string; ema50: number; distance_pct: number } | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/strategy/regime`).then(r => r.ok ? r.json() : null).then(setRegime).catch(() => {});
  }, []);

  const coinName = getCoinName(symbol, coinMeta);
  const displayName = coinName !== symbol ? coinName : symbol.replace("/USDT", "");

  if (isLoading && !details) {
    return (
      <div className="p-4 flex flex-col gap-4 border-t border-border bg-secondary shrink-0">
        <div className="flex gap-3 items-center">
          <Skeleton className="w-8 h-8 rounded-full" />
          <div className="space-y-1.5">
            <Skeleton className="w-20 h-4" />
            <Skeleton className="w-14 h-3" />
          </div>
        </div>
        <Skeleton className="w-32 h-7" />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="w-full h-4" />)}
        </div>
      </div>
    );
  }

  if (!details) return null;

  const isPositive = (details.change_24h || 0) >= 0;
  const priceRange = details.high_24h - details.low_24h;
  const currentPosition = priceRange > 0 ? ((details.price - details.low_24h) / priceRange) * 100 : 50;

  const titanSignal = titan?.signal ?? null;
  const titanConfidence = titan?.confidence ?? 0;
  const titanColor =
    titanSignal?.includes("BUY") ? "text-green-700 dark:text-green-400 bg-green-500/10 border-green-500/20" :
    titanSignal?.includes("SELL") ? "text-red-700 dark:text-red-400 bg-red-500/10 border-red-500/20" :
    "text-muted-foreground bg-muted/40 border-border/30";

  return (
    <div className="p-4 flex flex-col gap-4 border-t border-border bg-secondary shrink-0 overflow-y-auto scrollbar-thin scrollbar-thumb-muted">
      {/* Header */}
      <div className="flex items-center gap-3">
        <CoinIcon symbol={symbol} coinMeta={coinMeta} size={30} />
        <div>
          <div className="text-[16px] font-bold text-foreground leading-tight">{displayName}</div>
          <div className="text-[11px] text-muted-foreground">{symbol}</div>
        </div>
      </div>

      {/* Price */}
      <div className="flex items-baseline gap-3">
        <div className="text-[22px] font-extrabold text-foreground tracking-tight font-mono">
          ${details.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}
        </div>
        <div className={cn("flex items-center gap-1 text-[13px] font-bold px-2 py-0.5 rounded-md", isPositive ? "text-success bg-success/15" : "text-danger bg-danger/15")}>
          {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {formatChange(details.change_24h)}
        </div>
      </div>

      {/* Stats */}
      <div className="flex flex-col gap-1.5">
        <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1">24H Stats</div>
        {[
          { label: "Volume", value: formatVolume(details.volume_24h) },
          { label: "High", value: `$${details.high_24h?.toLocaleString(undefined, { maximumFractionDigits: 6 })}` },
          { label: "Low", value: `$${details.low_24h?.toLocaleString(undefined, { maximumFractionDigits: 6 })}` },
        ].map((stat) => (
          <div key={stat.label} className="flex justify-between items-center py-0.5">
            <span className="text-[12px] text-muted-foreground">{stat.label}</span>
            <span className="text-[12px] font-bold text-foreground font-mono">{stat.value}</span>
          </div>
        ))}
      </div>

      {/* Price Position Bar */}
      <div className="space-y-1.5">
        <div className="h-1.5 w-full bg-muted rounded-full relative overflow-visible">
          <div className="h-full bg-gradient-to-r from-danger to-success rounded-full" />
          <div
            className="absolute top-1/2 w-3 h-3 bg-foreground border-2 border-secondary rounded-full -translate-y-1/2 -translate-x-1/2 transition-all duration-500 shadow-sm"
            style={{ left: `${Math.min(100, Math.max(0, currentPosition))}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] font-bold text-muted-foreground font-mono">
          <span>${details.low_24h?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
          <span>${details.high_24h?.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
        </div>
      </div>

      {/* Titan Signal */}
      <div className="border-t border-border/50 pt-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
            <Zap size={10} className="text-primary" />
            Analysis
          </div>
          {regime && (
            <span className={cn(
              "text-[9px] font-black px-1.5 py-0.5 rounded uppercase tracking-wider",
              regime.regime === "BULL" ? "bg-green-500/15 text-green-600 dark:text-green-400" : "bg-red-500/15 text-red-600 dark:text-red-400"
            )}>
              {regime.regime}
            </span>
          )}
        </div>

        {titanLoading && !titan ? (
          <div className="space-y-2">
            <Skeleton className="w-full h-8 rounded-lg" />
            <Skeleton className="w-full h-8 rounded-lg" />
          </div>
        ) : titan ? (
          <div className="space-y-2">
            {/* Titan Signal */}
            {titanSignal && (
              <div className={cn("flex items-center justify-between p-2.5 rounded-lg border", titanColor)}>
                <div>
                  <div className="text-[9px] font-bold opacity-70 uppercase tracking-widest mb-0.5">Titan Signal</div>
                  <span className="text-sm font-black">{titanSignal.replace(/_/g, " ")}</span>
                </div>
                <div className="text-right">
                  <div className="text-[9px] font-bold opacity-70 uppercase tracking-widest mb-0.5">Confidence</div>
                  <span className="text-sm font-black font-mono">{titanConfidence}</span>
                </div>
              </div>
            )}

            {/* Momentum */}
            {titan?.momentum && (
              <div className="text-[10px] text-muted-foreground px-1">
                Momentum: <span className="font-bold text-foreground">{titan.momentum.status}</span>
                {titan.momentum.is_overbought && " · Overbought"}
                {titan.momentum.is_oversold && " · Oversold"}
              </div>
            )}

            {/* Deep Analysis button */}
            <button
              onClick={() => setIsAnalysisOpen(true)}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-border/60 bg-muted/30 hover:bg-muted/60 hover:border-border transition-colors text-[11px] font-bold text-muted-foreground hover:text-foreground"
            >
              <BarChart2 size={11} />
              Deep Analysis
            </button>
          </div>
        ) : (
          <p className="text-[11px] text-muted-foreground/50 text-center py-2">Signal data unavailable</p>
        )}
      </div>

      {titan && (
        <CoinAnalysisModal
          isOpen={isAnalysisOpen}
          onClose={() => setIsAnalysisOpen(false)}
          symbol={symbol}
          timeframe={timeframe}
          titan={titan}
          regime={regime?.regime ?? "UNKNOWN"}
        />
      )}
    </div>
  );
}
