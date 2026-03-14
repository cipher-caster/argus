"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { useMarketIndicators } from "@/hooks/useMarketIndicators";
import { formatVolume } from "@/lib/formatters";
import { cn } from "@/lib/utils";

interface PulseStatProps {
  label: string;
  value: string;
  status: string;
  statusColor: string;
}

function PulseStat({ label, value, status, statusColor }: PulseStatProps) {
  return (
    <div className="flex flex-col gap-0.5">
      <div className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-sm font-black font-mono">{value}</span>
        <span className={cn("text-[9px] font-bold uppercase tracking-wide", statusColor)}>{status}</span>
      </div>
    </div>
  );
}

export function MarketPulseStrip() {
  const { data, isLoading } = useMarketIndicators();

  if (isLoading) return <Skeleton className="h-14 rounded-xl" />;
  if (!data) return null;

  const rsiValue = data.average_rsi?.value ?? 0;
  const rsiStatus = rsiValue > 70 ? "Overbought" : rsiValue < 30 ? "Oversold" : "Neutral";
  const rsiColor = rsiValue > 70 ? "text-red-400" : rsiValue < 30 ? "text-green-400" : "text-muted-foreground";

  const capRegime = data.total_market_cap?.regime ?? "NEUTRAL";
  const capColor = capRegime === "BULLISH" ? "text-green-400" : capRegime === "BEARISH" ? "text-red-400" : "text-muted-foreground";

  const domValue = data.btc_dominance?.value ?? 0;
  const domStatus = domValue > 55 ? "BTC Heavy" : domValue < 45 ? "Alt Season" : "Balanced";
  const domColor = domValue > 55 ? "text-yellow-400" : domValue < 45 ? "text-purple-400" : "text-muted-foreground";

  return (
    <div className="bg-secondary/20 border border-border/30 rounded-xl px-6 py-3 flex items-center justify-between flex-wrap gap-x-8 gap-y-3">
      <PulseStat label="Avg RSI" value={rsiValue.toFixed(1)} status={rsiStatus} statusColor={rsiColor} />
      <div className="h-6 w-px bg-border/40 hidden sm:block" />
      <PulseStat label="Market Cap" value={formatVolume(data.total_market_cap?.value ?? 0)} status={capRegime} statusColor={capColor} />
      <div className="h-6 w-px bg-border/40 hidden sm:block" />
      <PulseStat label="BTC Dom" value={`${domValue.toFixed(1)}%`} status={domStatus} statusColor={domColor} />
    </div>
  );
}
