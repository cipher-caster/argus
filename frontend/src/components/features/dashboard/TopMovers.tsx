"use client";

import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { Skeleton } from "@/components/ui/skeleton";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { useMarketSummary } from "@/hooks/useMarketOverview";
import { formatChange } from "@/lib/formatters";
import { CoinInfo } from "@/lib/marketApi";
import { cn } from "@/lib/utils";
import { TrendingDown, TrendingUp } from "lucide-react";
import Link from "next/link";

function MoverChip({ coin, type, coinMeta }: { coin: CoinInfo; type: "gain" | "loss"; coinMeta: any }) {
  const isGain = type === "gain";
  return (
    <Link
      href={`/chart/${coin.symbol.replace("/", "-")}`}
      className={cn(
        "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border transition-all duration-200 hover:scale-[1.02] shrink-0",
        isGain
          ? "bg-green-500/5 border-green-500/20 hover:bg-green-500/10 hover:border-green-500/40"
          : "bg-red-500/5 border-red-500/20 hover:bg-red-500/10 hover:border-red-500/40"
      )}
    >
      <CoinIcon symbol={coin.symbol} coinMeta={coinMeta} size={14} />
      <span className="text-xs font-bold leading-none">{coin.symbol.split("/")[0]}</span>
      <span className={cn("text-[11px] font-semibold font-mono", isGain ? "text-green-500" : "text-red-500")}>
        {formatChange(coin.change_24h)}
      </span>
    </Link>
  );
}

function MoverRow({ label, coins, type, coinMeta }: { label: string; coins: CoinInfo[]; type: "gain" | "loss"; coinMeta: any }) {
  const isGain = type === "gain";
  return (
    <div className="flex items-center gap-3">
      <div className={cn("flex items-center gap-1 text-[9px] font-black uppercase tracking-widest shrink-0 w-14", isGain ? "text-green-500/70" : "text-red-500/70")}>
        {isGain ? <TrendingUp size={9} /> : <TrendingDown size={9} />}
        {label}
      </div>
      <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none">
        {coins.map((coin) => (
          <MoverChip key={coin.symbol} coin={coin} type={type} coinMeta={coinMeta} />
        ))}
      </div>
    </div>
  );
}

export function TopMovers() {
  const { data, isLoading } = useMarketSummary();
  const { coinMeta } = useCoinMeta();

  if (isLoading) {
    return (
      <div className="bg-secondary/20 border border-border/30 rounded-xl px-4 py-3 space-y-2.5">
        {[0, 1].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="w-14 h-3 shrink-0" />
            <div className="flex gap-1.5">
              {Array.from({ length: 8 }).map((_, j) => <Skeleton key={j} className="h-7 w-20 rounded-lg shrink-0" />)}
            </div>
          </div>
        ))}
      </div>
    );
  }

  const gainers = (data?.top_gainers ?? []).slice(0, 10);
  const losers = (data?.top_losers ?? []).slice(0, 10);

  if (gainers.length === 0 && losers.length === 0) return null;

  return (
    <div className="bg-secondary/20 border border-border/30 rounded-xl px-4 py-3 space-y-2.5">
      <MoverRow label="Gainers" coins={gainers} type="gain" coinMeta={coinMeta} />
      <div className="h-px bg-border/30" />
      <MoverRow label="Losers" coins={losers} type="loss" coinMeta={coinMeta} />
    </div>
  );
}
