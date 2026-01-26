"use client";

import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { fetchTitanRadar, TitanRadarItem } from "@/lib/api";
import { formatPrice } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { ArrowDown, ArrowUp, Info, PauseCircle, RefreshCcw, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

export function TitanSignalsPanel({ timeframe = "4h" }: { timeframe?: string }) {
  const [data, setData] = useState<TitanRadarItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<number>(0);
  const { coinMeta } = useCoinMeta();

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await fetchTitanRadar(50, timeframe);

      const priority = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"];
      const filtered = res.data.filter((item) => {
        const normalized = item.symbol.replace("/", "");
        return priority.includes(normalized) || item.confidence >= 60;
      });

      filtered.sort((a, b) => {
        const normA = a.symbol.replace("/", "");
        const normB = b.symbol.replace("/", "");
        const pA = priority.indexOf(normA);
        const pB = priority.indexOf(normB);
        if (pA !== -1 && pB !== -1) return pA - pB;
        if (pA !== -1) return -1;
        if (pB !== -1) return 1;
        return b.confidence - a.confidence;
      });

      setData(filtered.slice(0, 8));
      setLastUpdated(res.last_updated);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60 * 1000);
    return () => clearInterval(interval);
  }, [timeframe]);

  if (loading && data.length === 0) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-48" />
        <div className="space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-16 w-full rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <ShieldCheck className="text-primary" size={20} />
            Titan Signals (Live)
            <button onClick={loadData} className="ml-1 p-1 hover:bg-muted rounded-full transition-colors text-muted-foreground/50 hover:text-primary" title="Refresh">
              <RefreshCcw size={14} />
            </button>
          </h2>
          <div className="flex items-center gap-2">
            <p className="text-xs text-muted-foreground">Predictive Entry Setups ({timeframe.toUpperCase()})</p>
            <span className="text-xs text-muted-foreground border-l border-border pl-2 ml-1">Updated: {new Date(lastUpdated).toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-border/50 shadow-sm">
        <table className="w-full text-sm text-left border-collapse">
          <thead>
            <tr className="bg-muted/30 border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
              <th className="px-4 py-3 font-semibold">Symbol</th>
              <th className="px-4 py-3 font-semibold text-right">Price</th>
              <th className="px-4 py-3 font-semibold text-center">Action</th>
              <th className="px-4 py-3 font-semibold text-center">Confidence</th>
              <th className="px-4 py-3 font-semibold text-right">Limit Entry</th>
              <th className="px-4 py-3 font-semibold text-center">Distance</th>
              <th className="px-4 py-3 font-semibold text-right">Targets (TP/SL)</th>
              <th className="px-4 py-3 font-semibold text-right">Logic</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/30">
            {data.map((item) => (
              <SignalRow key={item.symbol} item={item} coinMeta={coinMeta} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SignalRow({ item, coinMeta }: { item: TitanRadarItem; coinMeta: any }) {
  const isWait = item.signal.includes("WAIT");
  const isBuy = item.signal.includes("BUY");
  const isSell = item.signal.includes("SELL");

  const entryDiff = ((item.price - item.entry) / item.entry) * 100;

  return (
    <tr className="hover:bg-muted/20 transition-colors">
      <td className="px-4 py-3 font-bold">
        <Link href={`/chart/${item.symbol.replace("/", "-")}`} className="flex items-center gap-2 hover:text-primary transition-colors">
          <CoinIcon symbol={item.symbol} coinMeta={coinMeta} size={24} />
          <span>{item.symbol.split("/")[0]}</span>
        </Link>
      </td>
      <td className="px-4 py-3 text-right font-mono text-xs">{formatPrice(item.price)}</td>

      <td className="px-4 py-3 text-center">
        <div
          className={cn(
            "inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-[10px] font-black uppercase tracking-wide border mx-auto",
            isWait
              ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
              : isBuy
                ? "bg-green-500/10 text-green-500 border-green-500/20 shadow-[0_0_10px_-3px_rgba(34,197,94,0.3)]"
                : isSell
                  ? "bg-red-500/10 text-red-500 border-red-500/20 shadow-[0_0_10px_-3px_rgba(239,68,68,0.3)]"
                  : "bg-secondary text-muted-foreground",
          )}
        >
          {isWait ? <PauseCircle size={10} /> : isBuy ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
          {item.signal.replace("_", " ")}
        </div>
      </td>

      {/* Confidence Column */}
      <td className="px-4 py-3 text-center font-mono text-xs text-muted-foreground">{item.confidence}%</td>

      {/* Limit Entry Column */}
      <td className="px-4 py-3 text-right font-mono text-xs font-bold text-primary">{formatPrice(item.entry)}</td>

      {/* Distance Column */}
      <td className="px-4 py-3 text-center">
        <span className="text-[10px] text-muted-foreground bg-secondary/50 px-2 py-0.5 rounded">
          {Math.abs(entryDiff).toFixed(2)}% {entryDiff > 0 ? "Above" : "Below"}
        </span>
      </td>

      {/* Targets Column */}
      <td className="px-4 py-3 text-right">
        {!isWait ? (
          <div className="flex flex-col items-end gap-0.5 text-[10px] font-mono">
            <span className="text-green-500/80">TP: {formatPrice(item.tp)}</span>
            <span className="text-red-500/80">SL: {formatPrice(item.sl)}</span>
          </div>
        ) : (
          <span className="text-muted-foreground text-[10px]">-</span>
        )}
      </td>

      {/* Logic Column */}
      <td className="px-4 py-3 text-right">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex justify-end cursor-help">
                <Info size={14} className="text-muted-foreground hover:text-primary transition-colors" />
              </div>
            </TooltipTrigger>
            <TooltipContent className="max-w-[200px]">
              <ul className="list-disc pl-4 space-y-1 text-xs">
                {(item.reasons && item.reasons.length > 0 ? item.reasons : ["Trend Following Logic", "EMA 200 Confirmation"]).map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </td>
    </tr>
  );
}
