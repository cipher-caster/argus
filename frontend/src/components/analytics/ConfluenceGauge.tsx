"use client";

import { ConfluenceResponse, fetchConfluence } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { Moon, Waves, Zap } from "lucide-react";

export function ConfluenceGauge() {
  const { data, isLoading } = useQuery<ConfluenceResponse>({
    queryKey: ["confluence"],
    queryFn: () => fetchConfluence(50),
    refetchInterval: 60000,
  });

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
        <div className="text-right">
          <div className="text-2xl font-black">{data.metrics.bullish_pct}%</div>
          <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">Bullish Consensus</div>
        </div>
      </div>

      {/* Bars */}
      <div className="space-y-2">
        <div className="flex justify-between text-[10px] uppercase font-bold text-muted-foreground/70">
          <span>Sleep: {data.metrics.sleeping_pct}%</span>
          <span>Bear: {data.metrics.bearish_pct}%</span>
        </div>
        <div className="h-2 w-full bg-background/50 rounded-full overflow-hidden flex border border-white/5">
          <div style={{ width: `${data.metrics.sleeping_pct}%` }} className="bg-blue-500/50 h-full" />
          <div style={{ width: `${data.metrics.bullish_pct}%` }} className="bg-green-500 h-full" />
          <div style={{ width: `${data.metrics.bearish_pct}%` }} className="bg-red-500 h-full" />
        </div>
      </div>
    </div>
  );
}
