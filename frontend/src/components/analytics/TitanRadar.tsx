"use client";

import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { useToast } from "@/components/ui/toaster";
import { useTitanRadar } from "@/hooks/useAnalyticsData";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { formatPrice } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { ArrowDown, ArrowUp, Minus, RefreshCcw, Search, ShieldCheck, Zap } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

export function TitanRadar({ timeframe = "4h" }: { timeframe?: string }) {
  const [search, setSearch] = useState("");
  const { coinMeta } = useCoinMeta();
  const { toast, dismiss } = useToast();
  // Titan Radar defaults to 4h for best results (as per PDF "Titan Trend")
  const { data, isLoading, error, refetch, isRefetching } = useTitanRadar(50, timeframe);

  const handleRefresh = async () => {
    const id = toast("Refreshing Titan system...", "info");
    await refetch();
    dismiss(id);
    toast("Titan system updated", "success");
  };

  const filteredData = data?.data.filter((item) => item.symbol.toLowerCase().includes(search.toLowerCase())) || [];

  if (isLoading) return <div className="h-[500px] flex items-center justify-center">Loading Titan Radar...</div>;
  if (error) return <div className="h-[500px] flex items-center justify-center text-red-500">Error loading radar</div>;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <ShieldCheck className="text-primary" size={20} />
            Titan System Scanner
            <button onClick={handleRefresh} disabled={isRefetching} className="ml-1 p-1 hover:bg-muted rounded-full transition-colors text-muted-foreground/50 hover:text-primary disabled:opacity-50" title="Refresh">
              <RefreshCcw size={14} className={cn(isRefetching && "animate-spin")} />
            </button>
          </h2>
          <div className="flex items-center gap-2">
            <p className="text-xs text-muted-foreground">Unified Trend + Momentum Strategy ({timeframe.toUpperCase()})</p>
            {data?.last_updated && <span className="text-[10px] text-muted-foreground border-l border-border pl-2">Updated: {new Date(data.last_updated).toLocaleTimeString()}</span>}
          </div>
        </div>

        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={14} />
          <input
            type="text"
            placeholder="Search symbols..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 bg-background border border-border rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-border/50 shadow-sm">
        <table className="w-full text-sm text-left border-collapse">
          <thead>
            <tr className="bg-muted/30 border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
              <th className="px-4 py-3 font-semibold">Symbol</th>
              <th className="px-4 py-3 font-semibold text-right">Price</th>
              <th className="px-4 py-3 font-semibold text-center">Signal</th>
              <th className="px-4 py-3 font-semibold text-center">Trend (EMA)</th>
              <th className="px-4 py-3 font-semibold text-center">Momentum</th>
              <th className="px-4 py-3 font-semibold text-right">Targets</th>
              <th className="px-4 py-3 font-semibold text-right">Advice</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/30">
            {filteredData.map((item) => (
              <tr key={item.symbol} className="hover:bg-muted/20 transition-colors">
                <td className="px-4 py-3 font-bold">
                  <Link href={`/chart/${item.symbol.replace("/", "-")}`} className="flex items-center gap-2 hover:text-primary transition-colors">
                    <CoinIcon symbol={item.symbol} coinMeta={coinMeta} size={24} />
                    <span>{item.symbol.split("/")[0]}</span>
                  </Link>
                </td>
                <td className="px-4 py-3 text-right font-mono text-xs">{formatPrice(item.price)}</td>

                {/* Signal Badge */}
                <td className="px-4 py-3 text-center">
                  <div
                    className={cn(
                      "inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-[10px] font-black uppercase tracking-wide border",
                      item.signal.includes("BUY")
                        ? "bg-green-500/10 text-green-500 border-green-500/20 shadow-[0_0_10px_-3px_rgba(34,197,94,0.3)]"
                        : item.signal.includes("SELL")
                          ? "bg-red-500/10 text-red-500 border-red-500/20 shadow-[0_0_10px_-3px_rgba(239,68,68,0.3)]"
                          : "bg-secondary text-muted-foreground border-border",
                    )}
                  >
                    {item.signal.includes("BUY") ? <ArrowUp size={10} strokeWidth={3} /> : item.signal.includes("SELL") ? <ArrowDown size={10} strokeWidth={3} /> : <Minus size={10} />}
                    {item.signal.replace("_", " ")}
                    {item.confidence > 0 && <span className="opacity-70 ml-1">({item.confidence}%)</span>}
                  </div>
                </td>

                <td className="px-4 py-3 text-center">
                  <span className={cn("text-[10px] font-bold", item.trend === "BULLISH" ? "text-green-500" : "text-red-500")}>{item.trend}</span>
                </td>

                <td className="px-4 py-3 text-center">
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-[10px] font-medium">{item.momentum}</span>
                    {item.volatility === "SQUEEZE" && (
                      <span className="text-[9px] bg-purple-500/10 text-purple-400 px-1 rounded flex items-center gap-0.5">
                        <Zap size={8} /> SQZ
                      </span>
                    )}
                  </div>
                </td>

                <td className="px-4 py-3 text-right">
                  {item.entry > 0 ? (
                    <div className="flex flex-col items-end gap-0.5 text-[10px] font-mono">
                      <span className="text-green-500/80">TP: {formatPrice(item.tp)}</span>
                      <span className="text-red-500/80">SL: {formatPrice(item.sl)}</span>
                    </div>
                  ) : (
                    <span className="text-muted-foreground text-[10px]">-</span>
                  )}
                </td>

                <td className="px-4 py-3 text-right text-[10px] font-medium text-muted-foreground max-w-[150px] truncate">{item.advice}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-[10px] text-muted-foreground text-center italic opacity-60">* Based on EMA 200, RSI 14, MACD, and Bollinger Bands. Use strictly with risk management.</div>
    </div>
  );
}
