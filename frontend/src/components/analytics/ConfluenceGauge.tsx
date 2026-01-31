"use client";

import { useToast } from "@/components/ui/toaster";
import { ConfluenceResponse, fetchConfluence } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { Moon, RefreshCcw, Waves, Zap } from "lucide-react";

export function ConfluenceGauge() {
  const { toast, dismiss } = useToast();
  const { data, isLoading, refetch, isRefetching } = useQuery<ConfluenceResponse>({
    queryKey: ["confluence"],
    queryFn: () => fetchConfluence(50),
    refetchInterval: 60000,
  });

  const handleRefresh = async () => {
    const id = toast("Refreshing confluence data...", "info");
    await refetch();
    dismiss(id);
    toast("Confluence data updated", "success");
  };

  if (isLoading || !data) return <div className="h-32 bg-secondary/20 animate-pulse rounded-xl" />;

  const getVidudals = (verdict: string) => {
    switch (verdict) {
      case "SLEEPING":
        return { icon: Moon, color: "text-blue-400", bg: "bg-blue-500/10", label: "MARKET SLEEPING", desc: "Low Volatility. Stay Cash." };
      case "TSUNAMI_BULL":
        return { icon: Waves, color: "text-green-500", bg: "bg-green-500/10", label: "BULL TSUNAMI", desc: "Aggressive Longs Allowed." };
      case "TSUNAMI_BEAR":
        return { icon: Waves, color: "text-red-500", bg: "bg-red-500/10", label: "BEAR TSUNAMI", desc: "Aggressive Shorts Allowed." };
      default:
        return { icon: Zap, color: "text-yellow-500", bg: "bg-yellow-500/10", label: "CHOPPY / VOLATILE", desc: "Reduce Position Size." };
    }
  };

  const visuals = getVidudals(data.verdict);
  const Icon = visuals.icon;

  return (
    <div className={cn("bg-secondary/30 rounded-2xl p-6 border border-border/50 backdrop-blur-sm flex items-center justify-between gap-8", visuals.bg)}>
      {/* Left: Market State */}
      <div className="flex items-center gap-4">
        <div className={cn("p-3 rounded-xl bg-background/50 border border-border/50", visuals.color)}>
          <Icon size={32} />
        </div>
        <div>
          <div className={cn("text-lg font-black tracking-widest uppercase", visuals.color)}>{visuals.label}</div>
          <div className="text-sm text-muted-foreground font-medium">{visuals.desc}</div>
        </div>
      </div>

      {/* Center: Metrics */}
      <div className="flex items-center gap-8">
        {/* Bullish % */}
        <div className="text-center">
          <div className="text-3xl font-black text-green-500">{data.metrics.bullish_pct}%</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">Bullish</div>
        </div>

        {/* Bearish % */}
        <div className="text-center">
          <div className="text-3xl font-black text-red-500">{data.metrics.bearish_pct}%</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">Bearish</div>
        </div>

        {/* Sleeping % */}
        <div className="text-center">
          <div className="text-3xl font-black text-blue-400">{data.metrics.sleeping_pct}%</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">Sleeping</div>
        </div>
      </div>

      {/* Right: Progress Bar + Refresh */}
      <div className="flex items-center gap-4">
        <div className="w-64 space-y-2">
          <div className="h-3 w-full bg-background/50 rounded-full overflow-hidden flex border border-white/5">
            <div style={{ width: `${data.metrics.sleeping_pct}%` }} className="bg-blue-500/50 h-full" title={`Sleeping: ${data.metrics.sleeping_pct}%`} />
            <div style={{ width: `${data.metrics.bullish_pct}%` }} className="bg-green-500 h-full" title={`Bullish: ${data.metrics.bullish_pct}%`} />
            <div style={{ width: `${data.metrics.bearish_pct}%` }} className="bg-red-500 h-full" title={`Bearish: ${data.metrics.bearish_pct}%`} />
          </div>
          {data?.last_updated && <div className="text-[9px] text-muted-foreground font-medium text-center">Updated: {new Date(data.last_updated).toLocaleString()}</div>}
        </div>

        <button onClick={handleRefresh} disabled={isRefetching} className="p-2 rounded-md text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50" title="Refresh Data">
          <RefreshCcw size={18} className={cn(isRefetching && "animate-spin")} />
        </button>
      </div>
    </div>
  );
}
