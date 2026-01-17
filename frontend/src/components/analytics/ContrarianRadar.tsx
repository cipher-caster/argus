"use client";

import { useContrarianRadar } from "@/hooks/useAnalyticsData";
import { formatPrice } from "@/lib/formatters";
import { Gauge, MoveHorizontal } from "lucide-react";

export function ContrarianRadar({ timeframe = "1h", limit = 50 }: { timeframe?: string; limit?: number }) {
  const { data, isLoading, error } = useContrarianRadar(timeframe, limit);

  if (isLoading) return <div className="h-[400px] flex items-center justify-center">Loading Contrarian Radar...</div>;
  if (error) return <div className="h-[400px] flex items-center justify-center text-red-500">Error loading radar</div>;

  const opportunities = data?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Gauge size={16} className="text-purple-500" />
          ATR Extension Radar (Overstretched Pairs)
        </h3>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {opportunities.map((item: any) => (
          <div key={item.symbol} className="bg-secondary/20 rounded-2xl p-5 border border-border/50">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-500 font-black">{item.symbol[0]}</div>
                <div>
                  <div className="text-lg font-black">{item.symbol.replace("USDT", "")}</div>
                  <div className="text-[10px] text-muted-foreground font-bold">{item.opportunity} Extension</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-mono font-bold text-purple-500">{item.extension_atr.toFixed(1)}x ATR</div>
                <div className="text-[10px] text-muted-foreground uppercase font-extrabold">Deviation</div>
              </div>
            </div>

            {/* Reversion Map */}
            <div className="relative h-12 flex items-center mb-6">
              <div className="absolute inset-0 h-1 bg-muted rounded-full top-1/2 -translate-y-1/2" />
              <div className="absolute left-0 w-3 h-3 rounded-full bg-primary border-2 border-background" />
              <div className="absolute left-0 mt-8 text-[10px] font-bold text-muted-foreground">Price: {formatPrice(item.price)}</div>

              <div className="absolute left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-purple-500 border-2 border-background shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
              <div className="absolute left-1/2 -translate-x-1/2 mt-8 text-[10px] font-bold text-purple-500">Mean (EMA): {formatPrice(item.mean)}</div>

              <div className="absolute right-0 w-3 h-3 rounded-full bg-blue-500 border-2 border-background" />
              <div className="absolute right-0 mt-8 text-[10px] font-bold text-blue-500">Target: {formatPrice(item.target)}</div>

              <div className="absolute flex flex-col items-center group cursor-help transition-all" style={{ left: "25%" }}>
                <MoveHorizontal size={14} className="text-muted-foreground opacity-50" />
              </div>
            </div>

            <div className="flex gap-2 mt-12">
              <div className="flex-1 bg-background/40 p-2 rounded-lg border border-border/30 text-center">
                <div className="text-[10px] text-muted-foreground font-bold mb-1">Potential Gain</div>
                <div className="text-xs font-black text-green-500">+{((Math.abs(item.price - item.target) / item.price) * 100).toFixed(1)}%</div>
              </div>
              <div className="flex-1 bg-background/40 p-2 rounded-lg border border-border/30 text-center">
                <div className="text-[10px] text-muted-foreground font-bold mb-1">Time Horizon</div>
                <div className="text-xs font-black">2-5 Days</div>
              </div>
            </div>
          </div>
        ))}

        {opportunities.length === 0 && (
          <div className="col-span-full h-32 flex items-center justify-center border-2 border-dashed border-border/50 rounded-2xl text-muted-foreground text-sm">No extreme extensions detected. Markets are currently trading near their means.</div>
        )}
      </div>
    </div>
  );
}
