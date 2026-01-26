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

  if (isLoading || !data) return <div className="h-24 bg-secondary/20 animate-pulse rounded-xl" />;

  const getVidudals = (verdict: string) => {
    switch (verdict) {
      case "SLEEPING":
        return { icon: Moon, color: "text-blue-400", bg: "bg-secondary/20", label: "MARKET SLEEPING", desc: "Low Volatility. Stay Cash." };
      case "TSUNAMI_BULL":
        return { icon: Waves, color: "text-green-500", bg: "bg-secondary/20", label: "BULL TSUNAMI", desc: "Aggressive Longs Allowed." };
      case "TSUNAMI_BEAR":
        return { icon: Waves, color: "text-red-500", bg: "bg-secondary/20", label: "BEAR TSUNAMI", desc: "Aggressive Shorts Allowed." };
      default:
        return { icon: Zap, color: "text-yellow-500", bg: "bg-secondary/20", label: "CHOPPY / VOLATILE", desc: "Reduce Position Size." };
    }
  };

  const visuals = getVidudals(data.verdict);
  const Icon = visuals.icon;

  return (
    <div className="bg-secondary/30 rounded-2xl p-5 border border-border/50 backdrop-blur-sm flex flex-col justify-between mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={cn("p-2 rounded-xl bg-background/50 border border-border/50", visuals.color)}>
            <Icon size={24} />
          </div>
          <div>
            <div className={cn("text-xs font-black tracking-widest uppercase", visuals.color)}>{visuals.label}</div>
            <div className="text-[11px] text-muted-foreground font-medium">{visuals.desc}</div>
          </div>
        </div>

        {/* Refresh & Consensus */}
        <div className="text-right">
          <div className="flex items-center justify-end gap-2 mb-1">
            <button onClick={handleRefresh} disabled={isRefetching} className="text-muted-foreground hover:text-primary transition-colors p-1 disabled:opacity-50" title="Refresh">
              <RefreshCcw size={14} className={cn(isRefetching && "animate-spin")} />
            </button>
          </div>
          <div className="text-2xl font-black">{data.metrics.bullish_pct}%</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">Bullish Consensus</div>
        </div>
      </div>

      {/* Bars */}
      <div className="space-y-3">
        {/* Progress Bar */}
        <div className="h-4 w-full bg-background/50 rounded-full overflow-hidden flex border border-white/5 relative">
          {/* Tooltips or inline percentages could go here, but simple colors work best with a legend */}
          <div style={{ width: `${data.metrics.sleeping_pct}%` }} className="bg-blue-500/30 h-full border-r border-background/10" title={`Sleeping: ${data.metrics.sleeping_pct}%`} />
          <div style={{ width: `${data.metrics.bullish_pct}%` }} className="bg-green-500 h-full border-r border-background/10" title={`Bullish: ${data.metrics.bullish_pct}%`} />
          <div style={{ width: `${data.metrics.bearish_pct}%` }} className="bg-red-500 h-full" title={`Bearish: ${data.metrics.bearish_pct}%`} />
        </div>

        {/* Legend */}
        <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider">
          <div className="flex items-center gap-1.5 text-blue-400">
            <div className="w-2 h-2 rounded-full bg-blue-500/50" />
            <span>Sleep: {data.metrics.sleeping_pct}%</span>
          </div>
          <div className="flex items-center gap-1.5 text-green-500">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span>Bull: {data.metrics.bullish_pct}%</span>
          </div>
          <div className="flex items-center gap-1.5 text-red-500">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span>Bear: {data.metrics.bearish_pct}%</span>
          </div>
        </div>

        {/* Footer */}
        {data.last_updated && <div className="text-[9px] text-muted-foreground text-right border-t border-white/5 pt-2 mt-2">Last Updated: {new Date(data.last_updated).toLocaleTimeString()}</div>}
      </div>
    </div>
  );
}
