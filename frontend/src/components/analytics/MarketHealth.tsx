"use client";

import { useMarketHealth } from "@/hooks/useAnalyticsData";
import { MarketHealthResponse } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Activity, ShieldAlert, Zap } from "lucide-react";

export function MarketHealth({ timeframe = "1h", limit = 100 }: { timeframe?: string; limit?: number }) {
  const { data, isLoading, error } = useMarketHealth(timeframe, limit);

  if (isLoading) return <div className="h-[400px] flex items-center justify-center">Loading Market Health...</div>;
  if (error) return <div className="h-[400px] flex items-center justify-center text-red-500">Error loading health data</div>;

  const summary = (data as MarketHealthResponse)?.summary || { total_coins: 0, bullish_pct: 0, bearish_pct: 0, squeezing_pct: 0 };
  const volatility = (data as MarketHealthResponse)?.volatility || { DANGER: 0, ACTIVE: 0, STABLE: 0 };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Trend Health */}
      <div className="bg-secondary/20 rounded-2xl p-6 border border-border/50">
        <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
          <Activity size={16} className="text-primary" />
          Trend Health (Total: {summary.total_coins} Coins)
        </h3>

        <div className="space-y-6">
          <div>
            <div className="flex justify-between text-xs mb-2">
              <span className="text-green-500 font-bold">Bullish (Above 200D EMA)</span>
              <span>{summary.bullish_pct}%</span>
            </div>
            <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-green-500 transition-all duration-1000" style={{ width: `${summary.bullish_pct}%` }} />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-2">
              <span className="text-red-500 font-bold">Bearish (Below 200D EMA)</span>
              <span>{summary.bearish_pct}%</span>
            </div>
            <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-red-500 transition-all duration-1000" style={{ width: `${summary.bearish_pct}%` }} />
            </div>
          </div>

          <div className="pt-4 border-t border-border/30">
            <div className="flex justify-between items-center">
              <div className="text-xs text-muted-foreground">Coins in Volatility Squeeze</div>
              <div className="px-2 py-1 bg-purple-500/10 text-purple-500 text-xs font-bold rounded border border-purple-500/20">{summary.squeezing_pct}% SQUEEZING</div>
            </div>
          </div>
        </div>
      </div>

      {/* Volatility Regimes */}
      <div className="bg-secondary/20 rounded-2xl p-6 border border-border/50">
        <h3 className="text-sm font-semibold mb-6 flex items-center gap-2">
          <ShieldAlert size={16} className="text-orange-500" />
          Volatility Distribution
        </h3>

        <div className="grid grid-cols-3 gap-4 h-32 items-end">
          <VolBar label="STABLE" value={volatility.STABLE} color="bg-blue-500" />
          <VolBar label="ACTIVE" value={volatility.ACTIVE} color="bg-green-500" />
          <VolBar label="DANGER" value={volatility.DANGER} color="bg-red-500" />
        </div>

        <div className="mt-8 p-3 bg-orange-500/10 rounded-xl border border-orange-500/20 flex gap-3">
          <Zap size={18} className="text-orange-500 shrink-0" />
          <p className="text-[10px] text-muted-foreground leading-relaxed">
            <span className="font-bold text-orange-500 block mb-1">REGIME ADVICE</span>
            {volatility.DANGER > 30 ? "High market volatility detected. Reduce leverage and tighten stop losses across all positions." : "Stable market conditions. Trend following strategies have higher probability of success."}
          </p>
        </div>
      </div>
    </div>
  );
}

function VolBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex flex-col items-center gap-2 h-full justify-end">
      <div className="text-[10px] font-bold text-muted-foreground">{value}%</div>
      <div className={cn("w-full rounded-t-lg transition-all duration-1000 min-h-[4px]", color)} style={{ height: `${Math.max(value, 5)}%` }} />
      <div className="text-[10px] font-extrabold mt-1">{label}</div>
    </div>
  );
}
