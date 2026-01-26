"use client";

import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { useToast } from "@/components/ui/toaster";
import { useLiquiditySweeps } from "@/hooks/useAnalyticsData";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { formatPrice } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { ChevronRight, Droplets, RefreshCcw, Target } from "lucide-react";
import Link from "next/link";

export function LiquidityMap({ timeframe = "1h", limit = 50 }: { timeframe?: string; limit?: number }) {
  const { coinMeta } = useCoinMeta();
  const { toast, dismiss } = useToast();
  const { data, isLoading, error, refetch, isRefetching } = useLiquiditySweeps(timeframe, limit);

  const handleRefresh = async () => {
    const id = toast("Refreshing liquidity map...", "info");
    await refetch();
    dismiss(id);
    toast("Liquidity sweeps updated", "success");
  };

  if (isLoading) return <div className="h-[400px] flex items-center justify-center">Loading Liquidity Map...</div>;
  if (error) return <div className="h-[400px] flex items-center justify-center text-red-500">Error loading sweeps</div>;

  const sweeps = data?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Droplets size={16} className="text-blue-500" />
          Active Sweep & Reclaims (Smart Money Entries)
        </h3>
        <div className="flex items-center gap-3">
          {data?.last_updated && <span className="text-xs text-muted-foreground hidden sm:inline">Updated: {new Date(data.last_updated).toLocaleTimeString()}</span>}
          <button onClick={handleRefresh} disabled={isRefetching} className="text-muted-foreground hover:text-primary transition-colors disabled:opacity-50" title="Refresh">
            <RefreshCcw size={14} className={cn(isRefetching && "animate-spin")} />
          </button>
          <span className="text-xs text-muted-foreground">{sweeps.length} Opportunities detected</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sweeps.map((item: any) => (
          <div key={item.symbol} className="bg-secondary/20 rounded-2xl p-4 border border-border/50 hover:border-primary/30 transition-all group">
            <div className="flex justify-between items-start mb-4">
              <Link href={`/chart/${item.symbol.replace("/", "-")}`} className="flex items-center gap-2 group-hover:opacity-80 transition-opacity">
                <CoinIcon symbol={item.symbol} coinMeta={coinMeta} size={32} />
                <div>
                  <div className="text-lg font-black">{item.symbol.replace("USDT", "")}</div>
                  <div className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">{item.type}</div>
                </div>
              </Link>
              <div className={cn("px-2 py-1 rounded text-[10px] font-black", item.bull_sweep ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500")}>{item.bull_sweep ? "BULL SWEEP" : "BEAR SWEEP"}</div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center p-2 bg-background/50 rounded-lg border border-border/30">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Target size={12} />
                  Level
                </div>
                <div className="text-xs font-mono font-bold">{formatPrice(item.swept_level)}</div>
              </div>

              <Link href={`/chart/${item.symbol.replace("/", "-")}`} className="w-full flex items-center justify-center gap-2 py-2 bg-primary/10 hover:bg-primary/20 text-primary rounded-xl text-xs font-bold transition-colors">
                View Setup
                <ChevronRight size={14} />
              </Link>
            </div>
          </div>
        ))}

        {sweeps.length === 0 && <div className="col-span-full h-32 flex items-center justify-center border-2 border-dashed border-border/50 rounded-2xl text-muted-foreground text-sm">No active sweeps detected in the last 24 hours</div>}
      </div>

      <div className="p-4 bg-blue-500/5 rounded-2xl border border-blue-500/10">
        <h4 className="text-xs font-bold text-blue-500 mb-2 uppercase">Pro Intelligence</h4>
        <p className="text-xs text-muted-foreground leading-relaxed">
          Sweeps occur when price moves beyond a major structural level (Previous Weekly High/Low) into liquidity, then immediately reclaims the level. This often indicates institutional "fake-outs" and high probability reversals.
        </p>
      </div>
    </div>
  );
}
