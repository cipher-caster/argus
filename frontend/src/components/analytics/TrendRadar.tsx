"use client";

import { useToast } from "@/components/ui/toaster";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { fetchTrendRadar, TrendRadarResponse } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { Activity, Layers, RefreshCcw } from "lucide-react";
import Link from "next/link";
import { CoinIcon } from "../features/dashboard/CoinIcon";

export function TrendRadar() {
  const { coinMeta } = useCoinMeta();
  const { toast, dismiss } = useToast();
  const { data, isLoading, error, refetch, isRefetching } = useQuery<TrendRadarResponse>({
    queryKey: ["trend-radar"],
    queryFn: () => fetchTrendRadar(50),
    refetchInterval: 60000,
  });

  const handleRefresh = async () => {
    const id = toast("Refreshing trend radar...", "info");
    await refetch();
    dismiss(id);
    toast("Trend radar updated", "success");
  };

  if (isLoading) return <div className="p-10 text-center animate-pulse">Scanning the Trend...</div>;
  if (error) return <div className="p-10 text-center text-red-500">Failed to load Trend Radar</div>;
  if (!data) return null;

  // Group buckets
  const retesting = data.map.filter((i) => i.status === "RETESTING");
  const trending = data.map.filter((i) => i.status === "BULLISH");
  const flippening = data.map.filter((i) => i.status === "FLIPPENING");
  const extended = data.map.filter((i) => i.status === "OVEREXTENDED");
  const lost = data.map.filter((i) => i.status === "LOST");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Layers className="text-primary" />
          The Trend God (200 EMA Radar)
        </h2>
        <div className="flex items-center gap-4 text-xs font-medium text-muted-foreground">
          {data.last_updated && <span className="hidden sm:inline">Updated: {new Date(data.last_updated).toLocaleString()}</span>}
          <button onClick={handleRefresh} disabled={isRefetching} className="hover:text-primary transition-colors disabled:opacity-50" title="Refresh">
            <RefreshCcw size={14} className={cn(isRefetching && "animate-spin")} />
          </button>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-500" /> {data.summary.total_bullish || 0} Bullish
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-red-500" /> {data.summary.total_bearish || 0} Bearish
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Opportunities */}
        <div className="space-y-6">
          {/* Retest Zone - Priority */}
          <div className="bg-secondary/20 border border-border/50 rounded-xl p-4">
            <h3 className="text-sm font-bold text-green-500 mb-3 flex items-center gap-2">
              <div className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-green-500/10">
                <div className="h-2 w-2 rounded-full bg-green-500" />
              </div>
              RETEST ZONE (BUY THE DIP)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {retesting.length === 0 && <span className="text-xs text-muted-foreground">No retests detected.</span>}
              {retesting.map((item) => (
                <TrendCard key={item.symbol} item={item} coinMeta={coinMeta} color="text-green-500" />
              ))}
            </div>
          </div>

          {/* Flippening - Watch */}
          <div className="bg-secondary/20 border border-border/50 rounded-xl p-4">
            <h3 className="text-sm font-bold text-purple-500 mb-3 flex items-center gap-2">
              <Activity size={16} /> FLIPPENING (WATCH)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {flippening.length === 0 && <span className="text-xs text-muted-foreground">No setups detected.</span>}
              {flippening.map((item) => (
                <TrendCard key={item.symbol} item={item} coinMeta={coinMeta} color="text-purple-500" />
              ))}
            </div>
          </div>

          {/* Trending - Momentum */}
          <div className="bg-secondary/20 border border-border/50 rounded-xl p-4">
            <h3 className="text-sm font-bold text-blue-500 mb-3 flex items-center gap-2">
              <div className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-blue-500/10">
                <div className="h-2 w-2 rounded-full bg-blue-500" />
              </div>
              TRENDING (MOMENTUM)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {trending.length === 0 && <span className="text-xs text-muted-foreground">No trending assets.</span>}
              {trending.map((item) => (
                <TrendCard key={item.symbol} item={item} coinMeta={coinMeta} color="text-blue-500" />
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Risks & Avoid */}
        <div className="space-y-6">
          {/* Overextended - Risk */}
          <div className="bg-secondary/20 border border-border/50 rounded-xl p-4">
            <h3 className="text-sm font-bold text-yellow-500 mb-3 flex items-center gap-2">
              <div className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-yellow-500/10">
                <div className="h-2 w-2 rounded-full bg-yellow-500" />
              </div>
              OVEREXTENDED (RISK)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {extended.length === 0 && <span className="text-xs text-muted-foreground">No extensions detected.</span>}
              {extended.map((item) => (
                <TrendCard key={item.symbol} item={item} coinMeta={coinMeta} color="text-yellow-500" />
              ))}
            </div>
          </div>

          {/* Lost - Bearish */}
          <div className="bg-secondary/20 border border-border/50 rounded-xl p-4">
            <h3 className="text-sm font-bold text-red-500 mb-3 flex items-center gap-2">
              <div className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-red-500/10">
                <div className="h-2 w-2 rounded-full bg-red-500" />
              </div>
              LOST (MACRO BEAR)
            </h3>
            <p className="text-xs text-muted-foreground mb-4">Assets trading below the 200 EMA. Macro downtrend.</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {lost.map((item) => (
                <Link href={`/chart/${item.symbol}`} key={item.symbol}>
                  <div className="flex items-center gap-2 p-2 rounded hover:bg-white/5 border border-transparent hover:border-white/10 transition-colors cursor-pointer opacity-60 hover:opacity-100">
                    <CoinIcon symbol={item.symbol} coinMeta={coinMeta} size={20} />
                    <span className="text-xs font-mono">{item.symbol}</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TrendCard({ item, coinMeta, color }: { item: any; coinMeta: any; color?: string }) {
  const getTooltip = () => {
    if (item.status === "RETESTING") return "Long Setup: Pullback to 200 EMA support";
    if (item.status === "FLIPPENING") return "Watch: Price crossing 200 EMA";
    if (item.status === "BULLISH") return "Trend Follow: Established uptrend";
    if (item.status === "OVEREXTENDED") return `High Risk: ${item.distance_pct}% above EMA`;
    return "Bearish: Trading below 200 EMA";
  };

  return (
    <Link href={`/chart/${item.symbol}`} className="block">
      <div title={getTooltip()} className="bg-background/60 hover:bg-background p-3 rounded-lg border border-transparent hover:border-border transition-all flex items-center justify-between group cursor-pointer">
        <div className="flex items-center gap-2">
          <CoinIcon symbol={item.symbol} coinMeta={coinMeta} />
          <div>
            <div className="font-bold text-xs">{item.symbol}</div>
            <div className={`text-[10px] opacity-80 ${color}`}>
              {item.distance_pct > 0 ? "+" : ""}
              {item.distance_pct}% EMA
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs font-mono">{item.price}</div>
        </div>
      </div>
    </Link>
  );
}
