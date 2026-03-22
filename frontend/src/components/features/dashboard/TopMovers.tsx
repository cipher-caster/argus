"use client";

import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { Skeleton } from "@/components/ui/skeleton";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { useMarketSummary } from "@/hooks/useMarketOverview";
import { formatChange, formatPrice } from "@/lib/formatters";
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
        "flex items-center gap-2.5 px-3 py-2 rounded-xl border transition-all duration-200 hover:scale-[1.02] shrink-0",
        isGain
          ? "bg-green-500/5 border-green-500/20 hover:bg-green-500/10 hover:border-green-500/40"
          : "bg-red-500/5 border-red-500/20 hover:bg-red-500/10 hover:border-red-500/40"
      )}
    >
      <CoinIcon symbol={coin.symbol} coinMeta={coinMeta} size={20} />
      <div className="min-w-0">
        <div className="text-xs font-bold leading-none">{coin.symbol.split("/")[0]}</div>
        <div className="text-[10px] text-muted-foreground font-mono leading-none mt-0.5">${formatPrice(coin.price)}</div>
      </div>
      <span className={cn("text-xs font-medium font-mono", isGain ? "text-success" : "text-danger")}>
        {formatChange(coin.change_24h)}
      </span>
    </Link>
  );
}

function MoverRow({ label, coins, type, coinMeta }: { label: string; coins: CoinInfo[]; type: "gain" | "loss"; coinMeta: any }) {
  const isGain = type === "gain";
  return (
    <div className="flex items-center gap-3">
      <div className={cn("flex items-center gap-1 text-[9px] font-black uppercase tracking-widest shrink-0 w-16", isGain ? "text-green-500/70" : "text-red-500/70")}>
        {isGain ? <TrendingUp size={9} /> : <TrendingDown size={9} />}
        {label}
      </div>
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-none flex-1">
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
        <div className="flex items-center gap-3">
          <Skeleton className="w-16 h-3 shrink-0" />
          <div className="flex gap-2">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-10 w-[130px] rounded-xl shrink-0" />)}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Skeleton className="w-16 h-3 shrink-0" />
          <div className="flex gap-2">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-10 w-[130px] rounded-xl shrink-0" />)}
          </div>
        </div>
      </div>
    );
  }

  const gainers = (data?.top_gainers ?? []).slice(0, 5);
  const losers = (data?.top_losers ?? []).slice(0, 5);

  if (gainers.length === 0 && losers.length === 0) return null;

  return (
    <div className="bg-secondary/20 border border-border/30 rounded-xl px-4 py-3 space-y-2.5">
      <MoverRow label="Gainers" coins={gainers} type="gain" coinMeta={coinMeta} />
      <div className="h-px bg-border/30" />
      <MoverRow label="Losers" coins={losers} type="loss" coinMeta={coinMeta} />
    </div>
  );
}
