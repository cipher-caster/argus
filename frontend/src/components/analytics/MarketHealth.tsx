"use client";

import { useToast } from "@/components/ui/toaster";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useMarketHealth } from "@/hooks/useAnalyticsData";
import { MarketHealthResponse } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Activity, HelpCircle, RefreshCcw, ShieldAlert, Zap } from "lucide-react";

export function MarketHealth({ timeframe = "1h", limit = 100 }: { timeframe?: string; limit?: number }) {
  const { toast, dismiss } = useToast();
  const { data, isLoading, error, refetch, isRefetching } = useMarketHealth(timeframe, limit);

  const handleRefresh = async () => {
    const id = toast("Refreshing market health...", "info");
    await refetch();
    dismiss(id);
    toast("Market health updated", "success");
  };

  if (isLoading) return <div className="h-[400px] flex items-center justify-center">Loading Market Health...</div>;
  if (error) return <div className="h-[400px] flex items-center justify-center text-red-500">Error loading health data</div>;

  const summary = (data as MarketHealthResponse)?.summary || { total_coins: 0, bullish_pct: 0, bearish_pct: 0, squeezing_pct: 0 };
  const volatility = (data as MarketHealthResponse)?.volatility || { DANGER: 0, ACTIVE: 0, STABLE: 0 };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Trend Health */}
      <div className="bg-secondary/20 rounded-2xl p-6 border border-border/50 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Activity size={16} className="text-primary" />
              Trend Health <span className="text-muted-foreground font-normal">({summary.total_coins} Coins)</span>
              <button onClick={handleRefresh} disabled={isRefetching} className="ml-2 text-muted-foreground hover:text-primary transition-colors disabled:opacity-50" title="Refresh Data">
                <RefreshCcw size={14} className={cn(isRefetching && "animate-spin")} />
              </button>
            </h3>
            <div className="flex items-center gap-2">
              {data?.last_updated && <span className="text-[10px] text-muted-foreground hidden sm:block">Updated: {new Date(data.last_updated).toLocaleTimeString()}</span>}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <HelpCircle size={14} className="text-muted-foreground hover:text-foreground transition-colors" />
                  </TooltipTrigger>
                  <TooltipContent className="max-w-[250px]">Percentage of coins trading above their 200-Day Exponential Moving Average (EMA). &gt;50% indicates a broad bull market.</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>

          <div className="space-y-8">
            <div className="space-y-2">
              <div className="flex justify-between items-end">
                <span className="text-xs font-bold text-green-500 uppercase tracking-wider">Bullish Regime</span>
                <span className="text-sm font-black text-foreground">{summary.bullish_pct}%</span>
              </div>
              <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                <div className="h-full bg-green-500 transition-all duration-1000 ease-out" style={{ width: `${summary.bullish_pct}%` }} />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-end">
                <span className="text-xs font-bold text-red-500 uppercase tracking-wider">Bearish Regime</span>
                <span className="text-sm font-black text-foreground">{summary.bearish_pct}%</span>
              </div>
              <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                <div className="h-full bg-red-500 transition-all duration-1000 ease-out" style={{ width: `${summary.bearish_pct}%` }} />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-4 border-t border-border/30 flex justify-between items-center">
          <div className="text-xs font-medium text-muted-foreground">Volatility Squeeze</div>
          <div className={cn("px-3 py-1 rounded-lg text-xs font-bold border transition-colors", summary.squeezing_pct > 0 ? "bg-purple-500/10 text-purple-500 border-purple-500/20" : "bg-muted text-muted-foreground border-transparent")}>
            {summary.squeezing_pct}% Squeezing
          </div>
        </div>
      </div>

      {/* Volatility Regimes */}
      <div className="bg-secondary/20 rounded-2xl p-6 border border-border/50 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <ShieldAlert size={16} className="text-orange-500" />
              Volatility Distribution
            </h3>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <HelpCircle size={14} className="text-muted-foreground hover:text-foreground transition-colors" />
                </TooltipTrigger>
                <TooltipContent className="max-w-[250px]">Categorizes market volatility based on daily price ranges. {"'Danger'"} implies high risk of liquidation.</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          <div className="grid grid-cols-3 gap-6 h-32 items-end px-2">
            <VolBar label="STABLE" value={volatility.STABLE} color="bg-blue-500" shadow="" />
            <VolBar label="ACTIVE" value={volatility.ACTIVE} color="bg-green-500" shadow="" />
            <VolBar label="DANGER" value={volatility.DANGER} color="bg-orange-500" shadow="" />
          </div>
        </div>

        <div className="mt-6 p-4 bg-orange-500/5 rounded-xl border border-orange-500/10 flex gap-3 backdrop-blur-sm">
          <Zap size={18} className="text-orange-500 shrink-0 mt-0.5" />
          <div>
            <div className="text-[10px] font-black text-orange-500 uppercase tracking-widest mb-1">Regime Advice</div>
            <p className="text-[11px] text-muted-foreground font-medium leading-relaxed">
              {volatility.DANGER > 30
                ? "High volatility environment. Risk of liquidation is elevated. Reduce position sizing and widen stop-losses."
                : "Market conditions are stable. favorable for trend following strategies and standard risk management."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function VolBar({ label, value, color, shadow }: { label: string; value: number; color: string; shadow: string }) {
  return (
    <div className="flex flex-col items-center gap-2 h-full justify-end group">
      <div className="text-[10px] font-bold text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity -mb-1">{value}%</div>
      <div className={cn("w-full rounded-t-lg transition-all duration-1000 min-h-[4px] relative", color, shadow)} style={{ height: `${Math.max(value, 5)}%` }} />
      <div className="text-[10px] font-extrabold text-muted-foreground group-hover:text-foreground transition-colors mt-1">{label}</div>
    </div>
  );
}
