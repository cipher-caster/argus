"use client";

import { CoinIcon } from "@/components/features/dashboard/CoinIcon";
import { useBestSetups } from "@/hooks/useAnalyticsData";
import { useCoinMeta } from "@/hooks/useCoinMeta";
import { BestSetupItem } from "@/lib/api";
import { cn } from "@/lib/utils";
import { RefreshCw, TrendingDown, TrendingUp } from "lucide-react";
import Link from "next/link";

function pct(from: number, to: number) {
  return (((to - from) / from) * 100).toFixed(1);
}

function formatPrice(price: number) {
  if (price >= 1000) return price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (price >= 1) return price.toFixed(4);
  return price.toFixed(6);
}

function SetupCard({ item, coinMeta }: { item: BestSetupItem; coinMeta: any }) {
  const isLong = item.direction === "LONG";
  const tpPct = isLong ? pct(item.entry, item.tp) : pct(item.tp, item.entry);
  const slPct = isLong ? pct(item.entry, item.sl) : pct(item.sl, item.entry);

  return (
    <Link href={`/chart/${item.symbol.replace("/", "-")}`} className="block group">
      <div className="bg-secondary/30 border border-border/50 rounded-2xl p-5 hover:border-primary/40 hover:bg-secondary/50 transition-all duration-300 space-y-4">
        {/* Header row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CoinIcon symbol={item.symbol} coinMeta={coinMeta} size={36} className="rounded-xl" />
            <div>
              <span className="font-black text-sm tracking-tight group-hover:text-primary transition-colors">
                {item.symbol.replace("USDT", "")}
              </span>
              <p className="text-xs text-muted-foreground font-mono">${formatPrice(item.entry)}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-black uppercase tracking-widest",
                isLong ? "bg-green-500/15 text-green-400" : "bg-red-500/15 text-red-400"
              )}
            >
              {isLong ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {item.direction}
            </span>
          </div>
        </div>

        {/* Conviction bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            <span>Conviction</span>
            <span className={cn(item.conviction >= 80 ? "text-green-400" : item.conviction >= 65 ? "text-yellow-400" : "text-muted-foreground")}>
              {item.conviction}%
            </span>
          </div>
          <div className="h-1.5 bg-muted/40 rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-700",
                item.conviction >= 80 ? "bg-green-500" : item.conviction >= 65 ? "bg-yellow-500" : "bg-primary/60"
              )}
              style={{ width: `${item.conviction}%` }}
            />
          </div>
        </div>

        {/* Entry / TP / SL */}
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="bg-muted/20 rounded-xl p-2.5">
            <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground mb-1">Entry</p>
            <p className="text-xs font-bold font-mono">${formatPrice(item.entry)}</p>
          </div>
          <div className="bg-green-500/10 rounded-xl p-2.5">
            <p className="text-[9px] font-black uppercase tracking-widest text-green-500/70 mb-1">TP</p>
            <p className="text-xs font-bold font-mono text-green-400">
              ${formatPrice(item.tp)}
              <span className="block text-[9px] text-green-500/60">+{tpPct}%</span>
            </p>
          </div>
          <div className="bg-red-500/10 rounded-xl p-2.5">
            <p className="text-[9px] font-black uppercase tracking-widest text-red-500/70 mb-1">SL</p>
            <p className="text-xs font-bold font-mono text-red-400">
              ${formatPrice(item.sl)}
              <span className="block text-[9px] text-red-500/60">{slPct}%</span>
            </p>
          </div>
        </div>

        {/* Eliz + Mayne MTF confluence */}
        {item.timeframe_confirmation && (
          <div className="border-t border-border/30 pt-3 space-y-1.5">
            <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground">MTF Confluence</p>
            <div className="flex items-center gap-3">
              {/* Eliz lane */}
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-black text-muted-foreground/60 uppercase tracking-widest">Eliz</span>
                {(["4h", "1d"] as const).map((tf) => (
                  <span
                    key={tf}
                    className={cn(
                      "text-[10px] font-black px-1.5 py-0.5 rounded",
                      item.timeframe_confirmation![tf]
                        ? "bg-green-500/15 text-green-400"
                        : "bg-muted/30 text-muted-foreground/50"
                    )}
                  >
                    {tf.toUpperCase()}
                  </span>
                ))}
              </div>
              <span className="text-muted-foreground/30 text-xs">|</span>
              {/* Mayne lane */}
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-black text-muted-foreground/60 uppercase tracking-widest">Mayne</span>
                {(["12h", "1w"] as const).map((tf) => (
                  <span
                    key={tf}
                    className={cn(
                      "text-[10px] font-black px-1.5 py-0.5 rounded",
                      item.timeframe_confirmation![tf]
                        ? "bg-green-500/15 text-green-400"
                        : "bg-muted/30 text-muted-foreground/50"
                    )}
                  >
                    {tf.toUpperCase()}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Historical win rate */}
        <div className="flex items-center justify-between border-t border-border/30 pt-3">
          <p className="text-[11px] text-muted-foreground leading-relaxed font-medium flex-1">
            {item.reason}
          </p>
          <span
            className={cn(
              "ml-3 shrink-0 text-[10px] font-black px-2 py-0.5 rounded-md",
              item.win_rate == null
                ? "bg-muted/30 text-muted-foreground"
                : item.win_rate >= 50
                ? "bg-green-500/15 text-green-400"
                : item.win_rate >= 33
                ? "bg-yellow-500/15 text-yellow-400"
                : "bg-red-500/15 text-red-400"
            )}
            title={
              item.win_rate == null
                ? "Insufficient backtest data (<10 trades)"
                : `${item.total_trades} historical trades`
            }
          >
            {item.win_rate == null ? "— hist." : `${item.win_rate.toFixed(0)}% hist.`}
          </span>
        </div>
      </div>
    </Link>
  );
}

export function BestSetups({ timeframe = "4h" }: { timeframe?: string }) {
  const { coinMeta } = useCoinMeta();
  const { data, isLoading, isRefetching, refetch } = useBestSetups(timeframe);
  const items = data?.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-black uppercase tracking-widest flex items-center gap-2">
            <TrendingUp size={16} className="text-primary" />
            Best Setups
          </h3>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            {items.length > 0 ? `${items.length} high-conviction setup${items.length > 1 ? "s" : ""} found` : "Scanning markets…"}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isRefetching}
          className="flex items-center gap-1.5 text-[11px] font-bold text-muted-foreground hover:text-foreground transition-colors"
        >
          <RefreshCw size={13} className={cn(isRefetching && "animate-spin")} />
          Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-52 bg-secondary/20 rounded-2xl animate-pulse" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-center space-y-3">
          <div className="text-4xl">🔍</div>
          <p className="font-black text-sm uppercase tracking-widest">No setups right now</p>
          <p className="text-xs text-muted-foreground max-w-xs">
            Oracle and Titan don't agree on any high-conviction trade. Market may be ranging or both systems are waiting for better entries.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((item) => (
            <SetupCard key={item.symbol} item={item} coinMeta={coinMeta} />
          ))}
        </div>
      )}
    </div>
  );
}
