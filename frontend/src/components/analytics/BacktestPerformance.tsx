"use client";

import { useState } from "react";
import { useBacktestStats, useSignalLog } from "@/hooks/useAnalyticsData";
import { CoinBacktestStats, SignalLogItem } from "@/lib/api";
import { formatPriceCompact, formatDateTime } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { BarChart3, ArrowUpDown, Trophy, Target, TrendingUp, TrendingDown, ChevronRight } from "lucide-react";

type SortKey = "profit_r" | "win_rate" | "total";

function SignalDetail({ symbol }: { symbol: string }) {
  const { data, isLoading } = useSignalLog(symbol, "backtest", 200);

  if (isLoading) return <tr><td colSpan={7} className="py-4 text-center text-muted-foreground text-[11px]">Loading signals…</td></tr>;
  if (!data?.data.length) return <tr><td colSpan={7} className="py-4 text-center text-muted-foreground text-[11px]">No backtest signals found.</td></tr>;

  return (
    <tr>
      <td colSpan={7} className="p-0">
        <div className="bg-secondary/20 border-t border-border/20 px-6 py-3">
          <div className="overflow-x-auto rounded-xl border border-border/30">
            <table className="w-full">
              <thead>
                <tr className="bg-secondary/40 text-[9px] font-black uppercase tracking-widest text-muted-foreground">
                  <th className="py-2 px-3 text-left">Date</th>
                  <th className="py-2 px-3 text-left">Dir</th>
                  <th className="py-2 px-3 text-left">Entry</th>
                  <th className="py-2 px-3 text-left">TP</th>
                  <th className="py-2 px-3 text-left">SL</th>
                  <th className="py-2 px-3 text-left">Conv.</th>
                  <th className="py-2 px-3 text-left">Outcome</th>
                  <th className="py-2 px-3 text-left">Exit</th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((s) => {
                  const isLong = s.direction === "LONG";
                  const outcomeStyle =
                    s.outcome === "WIN" ? "text-emerald-500 bg-emerald-500/10" :
                    s.outcome === "LOSS" ? "text-red-500 bg-red-500/10" :
                    s.outcome === "REVIEW" ? "text-amber-500 bg-amber-500/10" :
                    "text-sky-500 bg-sky-500/10";
                  return (
                    <tr key={s.id} className="border-b border-border/10 text-[11px] hover:bg-secondary/10">
                      <td className="py-2 px-3 text-muted-foreground whitespace-nowrap">{formatDateTime(s.fired_at)}</td>
                      <td className="py-2 px-3">
                        <span className={cn("font-black text-[10px] px-1.5 py-0.5 rounded",
                          isLong ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                        )}>
                          {s.direction}
                        </span>
                      </td>
                      <td className="py-2 px-3 font-mono text-muted-foreground">${formatPriceCompact(s.entry)}</td>
                      <td className="py-2 px-3 font-mono text-emerald-600 dark:text-emerald-400">${formatPriceCompact(s.tp)}</td>
                      <td className="py-2 px-3 font-mono text-red-600 dark:text-red-400">${formatPriceCompact(s.sl)}</td>
                      <td className="py-2 px-3 font-bold text-muted-foreground">{s.conviction}</td>
                      <td className="py-2 px-3">
                        <span className={cn("text-[10px] font-black px-1.5 py-0.5 rounded-md", outcomeStyle)}>
                          {s.outcome}
                        </span>
                      </td>
                      <td className="py-2 px-3 font-mono text-muted-foreground">
                        {s.resolved_price ? `$${formatPriceCompact(s.resolved_price)}` : "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </td>
    </tr>
  );
}

function CoinRow({ coin, rank, expanded, onToggle }: { coin: CoinBacktestStats; rank: number; expanded: boolean; onToggle: () => void }) {
  const isProfitable = coin.profit_r > 0 && (coin.win_rate ?? 0) > 40;
  const isMarginal = (coin.win_rate ?? 0) > 33 && !isProfitable;
  const wr = coin.win_rate ?? 0;

  return (
    <>
    <tr
      onClick={onToggle}
      className={cn(
        "border-b border-border/20 hover:bg-secondary/30 transition-colors cursor-pointer",
        rank <= 3 && "bg-primary/[0.03]",
        expanded && "bg-secondary/20"
      )}
    >
      <td className="py-3.5 px-3 text-center">
        {rank <= 3 ? (
          <Trophy size={14} className={cn(
            rank === 1 ? "text-amber-400" : rank === 2 ? "text-zinc-400" : "text-amber-700"
          )} />
        ) : (
          <span className="text-[11px] font-bold text-muted-foreground/50">#{rank}</span>
        )}
      </td>
      <td className="py-3.5 px-3">
        <div className="flex items-center gap-1.5">
          <ChevronRight size={12} className={cn("text-muted-foreground transition-transform duration-200", expanded && "rotate-90")} />
          <span className="text-[14px] font-black tracking-tight">{coin.base}</span>
        </div>
      </td>
      <td className="py-3.5 px-3 min-w-[180px]">
        <div className="flex items-center gap-2">
          <div className="h-2.5 rounded-full bg-secondary/60 flex-1 overflow-hidden">
            <div
              className={cn("h-full rounded-full transition-all duration-500",
                wr >= 45 ? "bg-emerald-500" : wr >= 33 ? "bg-amber-500" : "bg-red-500"
              )}
              style={{ width: `${wr}%` }}
            />
          </div>
          <span className={cn("text-[12px] font-black min-w-[42px] text-right",
            wr >= 45 ? "text-emerald-500 dark:text-emerald-400" :
            wr >= 33 ? "text-amber-500 dark:text-amber-400" : "text-red-500 dark:text-red-400"
          )}>
            {wr}%
          </span>
        </div>
      </td>
      <td className="py-3.5 px-3">
        <div className="flex items-center gap-1">
          {coin.profit_r > 0 ? (
            <TrendingUp size={12} className="text-emerald-500" />
          ) : coin.profit_r < 0 ? (
            <TrendingDown size={12} className="text-red-500" />
          ) : null}
          <span className={cn("text-[14px] font-black",
            coin.profit_r > 0 ? "text-emerald-500 dark:text-emerald-400" :
            coin.profit_r < 0 ? "text-red-500 dark:text-red-400" : "text-muted-foreground"
          )}>
            {coin.profit_r > 0 ? "+" : ""}{coin.profit_r}R
          </span>
        </div>
      </td>
      <td className="py-3.5 px-3">
        <span className="text-[12px] font-bold">
          <span className="text-emerald-500">{coin.wins}W</span>
          <span className="text-muted-foreground/50 mx-0.5">/</span>
          <span className="text-red-500">{coin.losses}L</span>
        </span>
        <span className="text-[10px] text-muted-foreground ml-1.5">({coin.total})</span>
      </td>
      <td className="py-3.5 px-3">
        <div className="flex gap-1.5">
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            L {coin.long_wr ?? 0}%
          </span>
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-500/10 text-red-600 dark:text-red-400">
            S {coin.short_wr ?? 0}%
          </span>
        </div>
      </td>
      <td className="py-3.5 px-3">
        <span className={cn("text-[10px] font-black px-2 py-1 rounded-md",
          isProfitable ? "bg-emerald-500/10 text-emerald-500" :
          isMarginal ? "bg-amber-500/10 text-amber-500" : "bg-red-500/10 text-red-500"
        )}>
          {isProfitable ? "PROFITABLE" : isMarginal ? "MARGINAL" : "UNPROFITABLE"}
        </span>
      </td>
    </tr>
    {expanded && <SignalDetail symbol={coin.symbol} />}
    </>
  );
}

export function BacktestPerformance() {
  const { data, isLoading, isError } = useBacktestStats();
  const [sortBy, setSortBy] = useState<SortKey>("profit_r");
  const [expandedCoin, setExpandedCoin] = useState<string | null>(null);

  const sorted = [...(data?.coins ?? [])].sort((a, b) => {
    if (sortBy === "profit_r") return b.profit_r - a.profit_r;
    if (sortBy === "win_rate") return (b.win_rate ?? 0) - (a.win_rate ?? 0);
    return b.total - a.total;
  });

  const overall = data?.overall;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <BarChart3 size={20} className="text-primary" />
          <h2 className="text-base font-black tracking-tight uppercase">Backtest Performance</h2>
          <span className="text-[10px] text-muted-foreground font-bold bg-secondary/50 px-2 py-0.5 rounded-md">4H / 1 YEAR</span>
        </div>
        <div className="flex items-center gap-1.5">
          <ArrowUpDown size={11} className="text-muted-foreground" />
          {(["profit_r", "win_rate", "total"] as SortKey[]).map((key) => (
            <button
              key={key}
              onClick={() => setSortBy(key)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all",
                sortBy === key
                  ? "bg-primary text-primary-foreground shadow-md"
                  : "bg-secondary/40 text-muted-foreground hover:text-foreground hover:bg-secondary/70"
              )}
            >
              {key === "profit_r" ? "Profit" : key === "win_rate" ? "Win Rate" : "Signals"}
            </button>
          ))}
        </div>
      </div>

      {/* Overall stats */}
      {overall && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total Signals", value: overall.total_signals, cls: "text-foreground" },
            { label: "Coins Tested", value: overall.total_coins, cls: "text-foreground" },
            {
              label: "Overall WR",
              value: overall.win_rate !== null ? `${overall.win_rate}%` : "—",
              cls: overall.win_rate !== null
                ? (overall.win_rate >= 45 ? "text-emerald-500 dark:text-emerald-400"
                  : overall.win_rate >= 33 ? "text-amber-500 dark:text-amber-400"
                  : "text-red-500 dark:text-red-400")
                : "text-muted-foreground",
            },
            {
              label: "Total Profit",
              value: `${overall.profit_r > 0 ? "+" : ""}${overall.profit_r}R`,
              cls: overall.profit_r > 0 ? "text-emerald-500 dark:text-emerald-400"
                : overall.profit_r < 0 ? "text-red-500 dark:text-red-400"
                : "text-muted-foreground",
            },
          ].map(({ label, value, cls }) => (
            <div key={label} className="bg-secondary/30 rounded-xl p-3 border border-border/40 text-center">
              <div className={cn("text-xl font-black", cls)}>{value}</div>
              <div className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      {isLoading ? (
        <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">Loading backtest results...</div>
      ) : isError ? (
        <div className="h-48 flex items-center justify-center text-red-500 text-sm">Failed to load backtest stats.</div>
      ) : !sorted.length ? (
        <div className="h-48 flex flex-col items-center justify-center text-muted-foreground text-sm gap-2">
          <span className="text-3xl">📊</span>
          <span>No backtest data. Run the backtest script first.</span>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-border/40">
          <table className="w-full">
            <thead>
              <tr className="bg-secondary/40 border-b border-border/40 text-[10px] font-black uppercase tracking-widest text-muted-foreground">
                <th className="py-3 px-3 text-center w-12">#</th>
                <th className="py-3 px-3 text-left">Coin</th>
                <th className="py-3 px-3 text-left">Win Rate</th>
                <th className="py-3 px-3 text-left">Profit</th>
                <th className="py-3 px-3 text-left">W/L</th>
                <th className="py-3 px-3 text-left">L/S Split</th>
                <th className="py-3 px-3 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((coin, i) => (
                <CoinRow
                  key={coin.symbol}
                  coin={coin}
                  rank={i + 1}
                  expanded={expandedCoin === coin.symbol}
                  onToggle={() => setExpandedCoin(expandedCoin === coin.symbol ? null : coin.symbol)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-[10px] text-muted-foreground font-medium">
        <span><Target size={10} className="inline mr-1" />Break-even: 33.3% WR at 2:1 RR</span>
        <span className="text-emerald-500">PROFITABLE = WR &gt; 40% + positive R</span>
        <span className="text-amber-500">MARGINAL = WR &gt; 33%</span>
        <span className="text-red-500">UNPROFITABLE = WR &lt; 33% or negative</span>
      </div>
    </div>
  );
}
