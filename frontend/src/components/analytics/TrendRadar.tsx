"use client";

import { useCoinMeta } from "@/hooks/useCoinMeta";
import { fetchTrendRadar, TrendRadarResponse } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { Activity, Layers } from "lucide-react";
import Link from "next/link";
import { CoinIcon } from "../features/dashboard/CoinIcon";

export function TrendRadar() {
  const { coinMeta } = useCoinMeta();
  const { data, isLoading, error } = useQuery<TrendRadarResponse>({
    queryKey: ["trend-radar"],
    queryFn: () => fetchTrendRadar(50),
    refetchInterval: 60000,
  });

  if (isLoading) return <div className="p-10 text-center animate-pulse">Scanning the Trend...</div>;
  if (error) return <div className="p-10 text-center text-red-500">Failed to load Trend Radar</div>;
  if (!data) return null;

  const getBucketLabel = (bucket: string) => {
    switch (bucket) {
      case "RETESTING":
        return "🟢 RETEST ZONE (BUY)";
      case "BULLISH":
        return "🔵 TRENDING";
      case "OVEREXTENDED":
        return "⚠️ EXTENDED (RISK)";
      case "FLIPPENING":
        return "🔮 FLIPPENING (WATCH)";
      case "LOST":
        return "🔴 LOST (AVOID)";
      default:
        return bucket;
    }
  };

  // Order of rows
  const bucketsOrder = ["RETESTING", "FLIPPENING", "BULLISH", "OVEREXTENDED", "LOST"];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Layers className="text-primary" />
          The Trend God (200 EMA Radar)
        </h2>
        <div className="flex gap-4 text-xs font-medium text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-500" /> {data.summary.total_bullish || 0} Bullish
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-red-500" /> {data.summary.total_bearish || 0} Bearish
          </div>
        </div>
      </div>

      <div className="space-y-8">
        {bucketsOrder.map((bucketKey) => {
          const items = data.map.filter((i) => i.status === bucketKey);
          if (items.length === 0) return null; // Hide empty rows to save space

          return (
            <div key={bucketKey} className="space-y-3">
              <div className="flex items-center gap-2 border-b border-border/30 pb-2">
                <h3 className="text-sm font-black tracking-widest">{getBucketLabel(bucketKey)}</h3>
                <span className="text-xs font-medium text-muted-foreground bg-secondary/50 px-2 py-0.5 rounded-full">{items.length}</span>
              </div>

              <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-secondary scrollbar-track-transparent">
                {items.map((item) => (
                  <Link href={`/chart/${item.symbol}`} key={item.symbol} className="shrink-0">
                    <div className="w-[200px] h-[100px] bg-secondary/10 hover:bg-secondary/30 border border-border/50 hover:border-border rounded-xl p-4 transition-all flex flex-col justify-between group">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CoinIcon symbol={item.symbol} coinMeta={coinMeta} size={24} />
                          <span className="font-bold text-sm">{item.symbol}</span>
                        </div>
                        {bucketKey === "FLIPPENING" && <Activity size={14} className="text-purple-500 animate-pulse" />}
                      </div>

                      <div className="flex items-end justify-between">
                        <div className="text-xs text-muted-foreground group-hover:text-foreground transition-colors">
                          {item.distance_pct > 0 ? "+" : ""}
                          {item.distance_pct}% EMA
                        </div>
                        <div className="text-sm font-mono font-medium">{item.price.toFixed(item.price < 1 ? 4 : 2)}</div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-secondary/30 p-4 rounded-lg text-xs text-muted-foreground border border-border/50">
        <strong className="text-primary block mb-1">STRATEGY NOTE:</strong>
        "Retest Zone" coins are dipping into the 200 EMA (High R:R entries). "Overextended" coins are {">"}30% above EMA (Avoid longs). "Flippening" coins are fighting to reclaim or lose the trend right now.
      </div>
    </div>
  );
}
