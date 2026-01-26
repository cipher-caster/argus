"use client";

import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { useToast } from "@/components/ui/toaster";
import { useOracleScreener } from "@/hooks/useAnalyticsData";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { ScreenerItem } from "@/lib/api";
import { formatPrice } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { Minus, RefreshCcw, Search, TrendingDown, TrendingUp } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export function OracleScreener({ timeframe = "1h", limit = 50 }: { timeframe?: string; limit?: number }) {
  const [search, setSearch] = useState("");
  const { coinMeta } = useCoinMeta();
  const { data, isLoading, error, refetch, isRefetching } = useOracleScreener(timeframe, limit);
  const { toast, dismiss } = useToast();

  const handleRefresh = async () => {
    const id = toast("Refreshing screener data...", "info");
    await refetch();
    dismiss(id);
    toast("Screener data refreshed", "success");
  };

  const filteredData = data?.data.filter((item: ScreenerItem) => item.symbol.toLowerCase().includes(search.toLowerCase())) || [];

  if (isLoading) return <div className="h-[500px] flex items-center justify-center">Loading Screener...</div>;
  if (error) return <div className="h-[500px] flex items-center justify-center text-red-500">Error loading screener</div>;

  return (
    <div className="space-y-4">
      {/* Search Header */}
      <div className="flex items-center justify-between">
        <div className="relative w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
          <input
            type="text"
            placeholder="Search symbols..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
        </div>
        <div className="flex items-center gap-3">
          {data?.last_updated && <div className="text-xs text-muted-foreground">Updated: {new Date(data.last_updated).toLocaleString()}</div>}
          <button onClick={handleRefresh} disabled={isRefetching} className="p-1.5 hover:bg-muted rounded-lg transition-colors text-muted-foreground hover:text-foreground disabled:opacity-50" title="Refresh Data">
            <RefreshCcw size={14} className={cn(isRefetching && "animate-spin")} />
          </button>
          <div className="text-xs text-muted-foreground border-l border-border pl-3">{filteredData.length} symbols</div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-border/50">
        <table className="w-full text-sm text-left border-collapse">
          <thead>
            <tr className="bg-muted/30 border-b border-border">
              <th className="px-4 py-3 font-semibold">Symbol</th>
              <th className="px-4 py-3 font-semibold text-right">Price</th>
              <th className="px-4 py-3 font-semibold text-center">Score</th>
              <th className="px-4 py-3 font-semibold text-center">Bias</th>
              <th className="px-4 py-3 font-semibold text-center">State</th>
              <th className="px-4 py-3 font-semibold">Advice</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item: any) => (
              <tr key={item.symbol} className="border-b border-border/30 hover:bg-muted/20 transition-colors">
                <td className="px-4 py-3 font-bold">
                  <Link href={`/chart/${item.symbol.replace("/", "-")}`} className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                    <CoinIcon symbol={item.symbol} coinMeta={coinMeta} size={24} />
                    <span>{item.symbol.split("/")[0]}</span>
                  </Link>
                </td>
                <td className="px-4 py-3 text-right font-mono">{formatPrice(item.price)}</td>
                <td className="px-4 py-3 text-center">
                  <div
                    className={cn(
                      "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold",
                      Math.abs(item.score) >= 3 ? (item.score > 0 ? "bg-green-500/10 text-green-500 border border-green-500/20" : "bg-red-500/10 text-red-500 border border-red-500/20") : "bg-muted text-muted-foreground",
                    )}
                  >
                    {item.score > 0 ? <TrendingUp size={12} /> : item.score < 0 ? <TrendingDown size={12} /> : <Minus size={12} />}
                    {item.confidence}
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={cn("text-[10px] font-extrabold uppercase", item.bias === "BULLISH" ? "text-green-500" : "text-red-500")}>{item.bias}</span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={cn("px-2 py-0.5 rounded text-[10px] font-bold", item.state === "SQUEEZE" ? "bg-purple-500/10 text-purple-500 border border-purple-500/20" : "bg-blue-500/10 text-blue-500")}>{item.state}</span>
                </td>
                <td className="px-4 py-3 text-xs text-muted-foreground italic truncate max-w-[200px]">{item.advice}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
