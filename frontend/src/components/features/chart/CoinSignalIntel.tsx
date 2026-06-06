"use client";

import { useBacktestStats, useSignalLog } from "@/hooks/useAnalyticsData";
import { cn } from "@/lib/utils";
import { Activity, TrendingUp, TrendingDown } from "lucide-react";

interface CoinSignalIntelProps {
  symbol: string;
  currentPrice?: number;
}

export function CoinSignalIntel({ symbol, currentPrice }: CoinSignalIntelProps) {
  const symbolKey = symbol.replace("/", "");
  const { data: backtestData } = useBacktestStats();
  const { data: signalData } = useSignalLog(symbolKey, undefined, 10);

  const coinStats = backtestData?.coins?.find((c) => c.symbol === symbolKey);
  const signals = signalData?.data ?? [];
  const openSignals = signals.filter((s) => s.outcome === "OPEN");

  if (!coinStats && !openSignals.length) return null;

  const wr = coinStats?.win_rate ?? 0;
  const isProfitable = coinStats && coinStats.profit_r > 0 && wr > 40;
  const isMarginal = coinStats && wr > 33 && !isProfitable;

  return (
    <div className="px-4 py-3 border-t border-border/50 bg-secondary shrink-0 space-y-2">
      <div className="flex items-center gap-1.5 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
        <Activity size={10} className="text-primary" />
        Signal Track Record
      </div>

      {/* Compact stats row */}
      {coinStats && (
        <div className="flex items-center justify-between p-2 rounded-lg bg-muted/30 border border-border/50">
          <div className="flex items-center gap-2">
            <span className={cn("text-[11px] font-black",
              wr >= 45 ? "text-emerald-500" : wr >= 33 ? "text-amber-500" : "text-red-500"
            )}>
              {wr}% WR
            </span>
            <span className="text-muted-foreground/30">|</span>
            <span className={cn("text-[11px] font-black",
              coinStats.profit_r > 0 ? "text-emerald-500" : coinStats.profit_r < 0 ? "text-red-500" : "text-muted-foreground"
            )}>
              {coinStats.profit_r > 0 ? "+" : ""}{coinStats.profit_r}R
            </span>
            <span className="text-muted-foreground/30">|</span>
            <span className="text-[10px] text-muted-foreground font-bold">
              <span className="text-emerald-500">{coinStats.wins}W</span>/<span className="text-red-500">{coinStats.losses}L</span>
            </span>
          </div>
          <span className={cn("text-[8px] font-black px-1.5 py-0.5 rounded",
            isProfitable ? "bg-emerald-500/10 text-emerald-500" :
            isMarginal ? "bg-amber-500/10 text-amber-500" : "bg-red-500/10 text-red-500"
          )}>
            {isProfitable ? "PROFIT" : isMarginal ? "MARGINAL" : "UNPROFIT"}
          </span>
        </div>
      )}

      {/* Open signals summary */}
      {openSignals.length > 0 && (
        <div className="flex flex-col gap-1">
          {openSignals.map((s) => {
            const isLong = s.direction === "LONG";
            const distToTp = currentPrice
              ? isLong ? ((s.tp - currentPrice) / currentPrice * 100) : ((currentPrice - s.tp) / currentPrice * 100)
              : null;
            return (
              <div key={s.id} className="flex items-center justify-between p-2 rounded-lg bg-sky-500/[0.05] border border-sky-500/20">
                <div className="flex items-center gap-1.5">
                  <span className={cn("text-[9px] font-black px-1 py-0.5 rounded",
                    isLong ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                  )}>
                    {s.direction}
                  </span>
                  <span className="text-[10px] font-mono text-muted-foreground">${s.entry.toLocaleString(undefined, { maximumFractionDigits: 4 })}</span>
                </div>
                <div className="flex items-center gap-1.5 text-[9px] font-bold">
                  {distToTp !== null && (
                    <span className="text-emerald-500">TP {distToTp > 0 ? "+" : ""}{distToTp.toFixed(1)}%</span>
                  )}
                  <span className="text-sky-500 bg-sky-500/10 px-1 py-0.5 rounded">OPEN</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
