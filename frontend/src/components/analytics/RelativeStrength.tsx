"use client";

import { useRelativeStrength } from "@/hooks/useAnalyticsData";
import { RelativeStrengthItem } from "@/lib/api";
import { cn } from "@/lib/utils";
import { BarChart3, TrendingUp } from "lucide-react";

export function RelativeStrength({ timeframe = "1h", limit = 50 }: { timeframe?: string; limit?: number }) {
  const { data, isLoading, error } = useRelativeStrength(timeframe, limit);

  if (isLoading) return <div className="h-[400px] flex items-center justify-center">Loading Relative Strength...</div>;
  if (error) return <div className="h-[400px] flex items-center justify-center text-red-500">Error loading strength data</div>;

  const items = data?.data || [];
  const sortedItems = [...items].sort((a: RelativeStrengthItem, b: RelativeStrengthItem) => b.performance_relative_pct - a.performance_relative_pct);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <TrendingUp size={16} className="text-green-500" />
          Alpha Leaders (Altcoins vs BTC Cluster)
        </h3>
        <span className="text-xs text-muted-foreground font-mono">Benchmark: BTCUSDT 1.00x</span>
      </div>

      <div className="bg-secondary/20 rounded-2xl border border-border/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="bg-muted/30 border-b border-border">
                <th className="px-6 py-4 font-bold">Symbol</th>
                <th className="px-6 py-4 font-bold">Strength</th>
                <th className="px-6 py-4 font-bold text-center">Relative performance (24h)</th>
                <th className="px-6 py-4 font-bold text-right">BTC Ratio</th>
              </tr>
            </thead>
            <tbody>
              {sortedItems.map((item: any) => (
                <tr key={item.symbol} className="border-b border-border/30 hover:bg-muted/20 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-background border border-border flex items-center justify-center font-bold text-[10px]">{item.symbol.replace("USDT", "")}</div>
                      <span className="font-black text-xs">{item.symbol}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div
                      className={cn(
                        "inline-flex px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-tighter",
                        item.strength === "STRONG" ? "bg-green-500/10 text-green-500" : item.strength === "WEAK" ? "bg-red-500/10 text-red-500" : "bg-muted text-muted-foreground",
                      )}
                    >
                      {item.strength}
                    </div>
                  </td>
                  <td className="px-6 py-4 max-w-[200px]">
                    <div className="flex items-center gap-3">
                      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className={cn("h-full transition-all duration-1000", item.performance_relative_pct >= 0 ? "bg-green-500" : "bg-red-500")}
                          style={{
                            width: `${Math.min(Math.abs(item.performance_relative_pct), 100)}%`,
                            marginLeft: item.performance_relative_pct >= 0 ? "0" : "auto",
                          }}
                        />
                      </div>
                      <span className={cn("text-xs font-mono font-bold min-w-[50px] text-right", item.performance_relative_pct >= 0 ? "text-green-500" : "text-red-500")}>
                        {item.performance_relative_pct >= 0 ? "+" : ""}
                        {item.performance_relative_pct.toFixed(2)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="text-xs font-mono font-bold">{item.current_ratio.toFixed(6)}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-start gap-3 p-4 bg-muted/30 rounded-2xl border border-border/50">
        <BarChart3 size={18} className="text-primary shrink-0 mt-0.5" />
        <p className="text-xs text-muted-foreground leading-relaxed">
          Relative Strength measures which altcoins are actually gaining value when priced in Bitcoin. A positive relative performance indicates the coin is showing "Alpha"—outperforming the market leader.
        </p>
      </div>
    </div>
  );
}
